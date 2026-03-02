"""
职责：接收用户问题和运行角色二的代码获取结果，结合结果优化并回答用户问题。
"""

from langchain.agents import create_agent
from agents.llm import chat_model
from agents.role_prompts import role_3_prompts
from langchain.messages import SystemMessage, AIMessage
from sandbox.box_langchain import code_box
from langgraph.config import get_stream_writer  
from agents.writer_messages import Message
from time import time

tools = [code_box]

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
    writer(Message(type="assistant", content="最终回答...\n"))
    for mode, chunk in role_3.stream(
        input={"messages": state["messages"]},
        stream_mode=["messages"]
    ):
        message, metadata = chunk
        response += message.content
        writer(Message(type="assistant", content=message.content))
    writer(Message(type="assistant", content=f"\n回答完成，耗时{time() - start_time:.2f}秒\n"))
    return {"messages": [AIMessage(content=response)], "answer": response}