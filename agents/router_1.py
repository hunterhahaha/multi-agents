"""
职责：判断用户问题的意图；
"""

from agents.llm import chat_model
from pydantic import BaseModel, Field
from typing import Annotated
from agents.state_messages import StateMessages

class Intent(BaseModel):
    """
    意图判断结果
    """
    intent: Annotated[str, Field(
        description="下一个要执行的节点，根据用户意图在role_2（代码生成角色）和END（结束）之间做选择。",
        enum=["role_2", "END"],
        )
    ]

def intent_judge(state_messages: StateMessages):
    """
    判断用户问题的意图
    """
    prompt = """
    你是一个意图判断专家，负责根据用户问题判断其意图
    请判断用户问题的意图，将其分类为role_2（代码生成角色）或END（结束）。
    """
    llm = chat_model.with_structured_output(Intent)
    resp = llm.invoke(state_messages.messages[-1].content)
    return {"next_node": resp.intent}

def router_1_node(state: StateMessages):
    """
    路由节点
    """
    return state