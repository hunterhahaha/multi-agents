"""
职责：接收角色一的处理结果并生成相对应的可执行的python代码，以纯字符串的形式只输出代码内容。
"""

from llms.llm import chat_model
from agents.role_prompts import engineer_prompts
from agents.state_messages import StateMessages, TaskRecord
from langchain.messages import SystemMessage, HumanMessage
from langgraph.config import get_stream_writer  
from agents.writer_messages import Message
from sandbox.box_langchain import python_code_box
from tools.web_tools import final_answer
from pydantic import BaseModel

class CodeState(BaseModel):
    code: str = ""
    code_result: str = ""
    failure_count: int = 0

def engineer_node(state: StateMessages):
    task_result = ""
    task_success = False

    code_state = CodeState()

    writer = get_stream_writer()  

    tools = [python_code_box, final_answer]

    engineer = chat_model.bind_tools(tools)

    try:
        writer(Message(type="engineer", content="编码中...\n"))

        while True:
            input = [
                SystemMessage(
                    content=engineer_prompts.format(
                        task=state["task"],
                    )
                ),
                HumanMessage(content=f"用户原始问题：{state["question"]}"),
                HumanMessage(content=f"上一轮代码状态：{code_state.model_dump_json()}"),
            ]

            response = engineer.invoke(
                input=input,
            )

            import logging
            logging.info(f"llm回复：{response}\n")
            # 触发工具调用
            if response.tool_calls:
                tool_calls = response.tool_calls
                tool_name = tool_calls[0]["name"]
                tool_args = tool_calls[0]["args"]
                # 调用代码运行工具
                if tool_name == "python_code_box":
                    writer(Message(type="engineer", content="正在运行代码...\n"))

                    code_result = python_code_box.invoke(tool_args)
                    code_state.code = tool_args["code"]
                    code_state.code_result = code_result
                    # 截取报错信息
                    if code_result.startswith("Error:"):
                        code_state.failure_count += 1
                        writer(Message(type="engineer", content="代码运行出错，正在重试...\n"))
                    else:
                        writer(Message(type="engineer", content="代码运行成功...\n"))
                # 调用最终回答工具
                elif tool_name == "final_answer":
                    task_result = final_answer.invoke(tool_args)
                    if code_state.failure_count < 4:
                        task_success = True
                    else: 
                        task_success = False
                    break

    except Exception as e:
        writer(Message(type="engineer", content=f"编码出错...\n"))
        
        import logging
        logging.error(f"编码出错...\n", exc_info=True)

        task_result = str(e)
        task_success = False

    return {
        "task_history": [TaskRecord(
            worker="engineer",
            task=state["task"],
            task_result=task_result,
            task_success=task_success,
        )]
    }
    
