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
        description="下一个要执行的节点，根据用户意图在role_1（代码处理角色）和chat（聊天角色）之间做选择。",
        enum=["role_1", "chat"],
        )
    ]
    use_reasoner: Annotated[bool, Field(
        description="是否需要使用推理模型来判断意图",
        enum=[True, False],
        )
    ]

def intent_node(state_messages: StateMessages):
    """
    判断用户问题的意图，和是否需要使用推理模型。
    """
    prompt = """
    请判断用户问题的意图，将其分类为role_1（问题处理角色）或chat（聊天角色）。
    同时判断回答该问题是否需要使用推理模型，将其分类为True（需要）或False（不需要）。
    """
    print("意图判断中...")
    from time import time
    start_time = time()
    llm = chat_model.with_structured_output(Intent)
    response = llm.invoke(state_messages.messages[-1].content)
    print(f"意图判断耗时：{time() - start_time}秒")
    return {"next_node": response.intent, "use_reasoner": response.use_reasoner}
