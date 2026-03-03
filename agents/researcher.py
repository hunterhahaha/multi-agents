"""
职责：接收需要外部信息的问题，通过搜索引擎搜索并抓取页面内容，总结后回答。
"""
from langchain.agents import create_agent
from agents.llm import chat_model
from agents.role_prompts import researcher_prompts
from langgraph.config import get_stream_writer
from agents.writer_messages import Message
from agents.tools.web_tools import searxng_search, fetch_webpage
from langchain.messages import AIMessage, AIMessageChunk
from agents.state_messages import StateMessages
from time import time

tools = [searxng_search, fetch_webpage]

researcher_agent = create_agent(
    model=chat_model,
    tools=tools,
    system_prompt=researcher_prompts,
)

def researcher_node(state: StateMessages):
    writer = get_stream_writer()
    start_time = time()
    response = ""

    writer(Message(type="assistant", content="正在搜索...\n"))

    for mode, chunk in researcher_agent.stream(
        input={"messages": state["messages"]},
        stream_mode=["messages", "updates"]
    ):
        if mode == "messages":
            message, metadata = chunk
            if isinstance(message, AIMessageChunk):
                response += message.content
                writer(Message(type="assistant", content=message.content))
    
    writer(Message(type="assistant", content=f"\n搜索完成，耗时{time() - start_time:.2f}秒\n"))

    return {
        "messages": [AIMessage(content=response)],
        "answer": response,
        "next_node": "END",
    }