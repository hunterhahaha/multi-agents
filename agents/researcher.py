"""
职责：接收需要外部信息的问题，通过搜索引擎搜索并抓取页面内容，总结后回答。
"""
from llms.llm import chat_model
from agents.role_prompts import researcher_prompts
from langgraph.config import get_stream_writer
from agents.writer_messages import Message
from tools.web_tools import searxng_search, fetch_webpage, final_answer
from langchain.messages import HumanMessage, SystemMessage
from agents.state_messages import StateMessages, TaskRecord

def researcher_node(state: StateMessages):
    writer = get_stream_writer()

    tools = [searxng_search, fetch_webpage, final_answer]

    researcher = chat_model.bind_tools(tools)

    input=[
        SystemMessage(content=researcher_prompts), 
        HumanMessage(content=state["task"])
    ]

    task_result = ""
    task_success = False

    try:
        while True:
            response = researcher.invoke(
                input=input
            )

            if response.tool_calls:
                tool_calls = response.tool_calls
                tool_name = tool_calls[0]["name"]
                tool_args = tool_calls[0]["args"]

                if tool_name == "searxng_search":
                    writer(Message(type="researcher", content="正在搜索相关内容...\n"))
                    search_result = searxng_search.invoke(tool_args)
                    input.append(HumanMessage(content=f"搜索结果：{search_result}"))
                
                elif tool_name == "fetch_webpage":
                    writer(Message(type="researcher", content="正在抓取网页内容...\n"))
                    webpage_content = fetch_webpage.invoke(tool_args)
                    input.append(HumanMessage(content=f"网页内容：{webpage_content}"))

                elif tool_name == "final_answer":
                    task_result = final_answer.invoke(tool_args)
                    task_success = True
                    break

    except Exception as e:
        writer(Message(type="researcher", content=f"搜索出错...\n"))
        
        import logging
        logging.error(f"researcher_node 出错: {e}")

        task_result = str(e)
        task_success = False

    return {
        "task_history": [TaskRecord(
            worker="researcher",
            task=state["task"],
            task_result=task_result,
            task_success=task_success,
        )]
    }