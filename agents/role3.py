"""
agents.role3 的 Docstring
职责：接收用户问题和运行角色二的代码获取结果，结合结果优化并回答用户问题。
"""

from langchain.agents import create_agent
from agents.llm import llm
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

from sandbox.box_langchain import code_box

tools = [code_box]

role_3 = create_agent(
    model=llm,
    system_prompt="你是一个代码助手，负责接收用户问题和角色二生成的代码，运行代码并结合结果优化回答用户问题。",
    checkpointer=checkpointer,
    tools=tools
)

from agents.state_messages import StateMessages

def role_3_node(state: StateMessages):
    messages = state.messages
    response = role_3.invoke({"messages": messages})
    return {"answer": response['messages'][-1].content}