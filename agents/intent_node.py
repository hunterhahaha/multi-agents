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
    system_prompt = """
    判断用户意图，只输出一行，格式必须为：<intent>,<reasoner>；
    intent只能是role_1（代码处理角色）或chat（聊天角色）；
    reasoner只能是True或False；
    例如：role_1,True或chat,False
    注意：只能输出一行，不能有任何解释。
    """

    writer(Message(type="intent_judge", content="意图判断中...\n"))

    from time import time
    start_time = time()
    response = ""
    for chunk in chat_model.stream(
        [system_prompt, state["question"]]
    ):
        response += chunk.content
        if ("\n" in response) or (len(response) > 8):
            break
    writer(Message(type="intent_judge", content=f"耗时：{time() - start_time:.2f}秒\n"))
    result = response.split(",")
    return {"next_node": result[0], "use_reasoner": result[1]}