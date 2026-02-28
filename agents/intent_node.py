"""
职责：判断用户问题的意图；
"""

from agents.llm import chat_model
from pydantic import BaseModel, Field
from typing import Annotated
from agents.state_messages import StateMessages
from langgraph.config import get_stream_writer  
from agents.writer_messages import Message

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
        description="回答该问题是否需要推理模型：复杂逻辑分析、算法设计、深度推理为True；简单问答、闲聊为False",
        enum=[True, False],
        )
    ]

def intent_node(state: StateMessages):
    """                                                                                                                                                                                                                                                                                                                                          
    判断用户问题的意图，和是否需要使用推理模型。
    """
    writer = get_stream_writer()
    writer(Message(type="intent_judge", content="意图判断中...\n"))
    from time import time
    start_time = time()
    llm = chat_model.with_structured_output(Intent)
    response = llm.invoke(state.messages)
    writer(Message(type="intent_judge", content=f"耗时：{time() - start_time:.2f}秒\n"))
    return {"next_node": response.intent, "use_reasoner": response.use_reasoner}
