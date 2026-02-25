"""
agents.role2 的 Docstring
职责：接收角色一的处理结果并生成相对应的可执行的python代码，以纯字符串的形式只输出代码内容。
"""

from langchain.agents import create_agent
from agents.llm import llm
from langgraph.checkpoint.memory import InMemorySaver
from agents.role_prompts import role2_prompts

checkpointer = InMemorySaver()

role_2 = create_agent(
    model=llm,
    system_prompt=role2_prompts,
    checkpointer=checkpointer,
)

from agents.state_messages import StateMessages

def role_2_node(state: StateMessages):
    messages = state.messages
    response = role_2.invoke({"messages": messages})
    return {"code": response['messages'][-1].content}