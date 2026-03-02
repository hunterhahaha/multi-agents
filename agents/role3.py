"""
职责：接收用户问题和运行角色二的代码获取结果，结合结果优化并回答用户问题。
"""

from langchain.agents import create_agent
from agents.llm import chat_model
from agents.role_prompts import role_3_prompts
from langchain.messages import AIMessage, AIMessageChunk
from sandbox.box_langchain import python_code_box
from langgraph.config import get_stream_writer  
from agents.writer_messages import Message
from time import time

tools = [python_code_box]

role_3 = create_agent(
    model=chat_model,
    system_prompt=role_3_prompts,
    tools=tools
)

from agents.state_messages import StateMessages

def role_3_node(state: StateMessages):
    response = ""
    writer = get_stream_writer()  
    start_time = time()
    code_result = ""

    writer(Message(type="assistant", content="最终回答...\n"))

    for mode, chunk in role_3.stream(
        input={"messages": state["messages"]},
        stream_mode=["messages", "updates"]
    ):
        # 捕获工具调用信息
        if mode == "updates":
            if chunk.get("tools"):
                code_result = chunk["tools"]["messages"][0].content
                # 处理报错，执行反馈环
                if code_result.startswith("Error:"):
                    if state["retry_count"] < 2:
                        writer(
                            Message(
                                type="assistant", 
                                content=f"""
                                \n代码执行失败，耗时{time() - start_time:.2f}秒，
                                即将进行第{state['retry_count'] + 1}次重试
                                \n"""
                            )
                        )
                        return {
                            "next_node": "role_2",
                            "retry_count": state["retry_count"] + 1,
                            "code_error": code_result,
                        }
                    elif state["retry_count"] >= 3:
                        writer(
                            Message(
                                type="assistant", 
                                content=f"""
                                \n代码执行失败，耗时{time() - start_time:.2f}秒，已重试3次，仍未成功
                                \n报错原因如下：
                                \n{code_result}
                                \n""",
                            )
                        )
                        return {
                            "messages": [AIMessage(content=f"以下是代码执行失败的原因：\n{code_result}")],
                            "next_node": "END",
                            "retry_count": 0,
                            "code_error": code_result,
                        }
        # 正常处理信息
        if mode == "messages":
            message, metadata = chunk
            if type(message) == AIMessageChunk:
                response += message.content

                writer(Message(type="assistant", content=message.content)
                )

    # 正常执行
    writer(Message(type="assistant", content=f"\n回答完成，耗时{time() - start_time:.2f}秒\n"))
    return {
        "messages": [AIMessage(content=response)], 
        "answer": response,
        "code_error": "",
        "code_result": code_result,
        "retry_count": 0,
        "next_node": "END",
    }