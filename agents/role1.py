"""
agents.role1 的 Docstring
职责：处理用户的问题，将用户的问题清晰化和流程化，传递给后续的角色进行代码生成。
"""

from langchain.agents import create_agent
from agents.llm import llm
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

role_1 = create_agent(
    model=llm,
    system_prompt="你是一个代码助手，负责处理用户的问题，将用户的问题清晰化和流程化，传递给后续的角色进行代码生成。",
    checkpointer=checkpointer,
)

from agents.state_messages import StateMessages

def role_1_node(state: StateMessages):
    messages = state.messages
    response = role_1.invoke({"messages": messages})
    return {"messages": messages + [response['messages'][-1]]}