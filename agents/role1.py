"""
agents.role1 的 Docstring
职责：处理用户的问题，将用户的问题清晰化和流程化，传递给后续的角色进行代码生成。
"""

from langchain.agents import create_agent
from agents.llm import llm
from langgraph.checkpoint.memory import InMemorySaver
from agents.role_prompts import role1_prompts

checkpointer = InMemorySaver()

from pydantic import BaseModel, Field
from typing import TypedDict, Annotated

class agent_output(BaseModel):
    answer: Annotated[str, Field(description="用户问题的清晰化和流程化后的结果。")]
    next_node: Annotated[str, Field(
        description="下一个要执行的节点，根据用户意图在role_2（代码生成角色）和END（结束）之间做选择。",
        enum=["role_2", "END"],
        )
    ]

role_1 = create_agent(
    model=llm,
    system_prompt=role1_prompts,
    checkpointer=checkpointer,
    response_format=agent_output,
)

from agents.state_messages import StateMessages

def role_1_node(state: StateMessages):
    messages = state.messages
    response = role_1.invoke({"messages": messages})
    return {
        "messages": messages + [("assistant", response['structured_response'].answer)], 
        "next_node": response['structured_response'].next_node, 
        "answer": response['structured_response'].answer if response['structured_response'].next_node == "END" else "",
    }
