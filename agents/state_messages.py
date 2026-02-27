from typing import Annotated, List
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class StateMessages(BaseModel):
    """
    参数：
        question: 问题，用于存储用户的原始问题。
        messages: 消息列表，用于存储对话历史记录。
        code: 代码，用于存储生成的代码。
        code_result: 代码运行结果，用于存储运行生成的代码后的结果。
        answer: 回答，用于存储生成的回答。
        next_node: 下一个节点，用于存储下一个要执行的节点。
    """
    question: Annotated[str, Field(default="")]
    messages: Annotated[List[BaseMessage], add_messages]
    code: Annotated[str, Field(default="")]
    answer: Annotated[str, Field(default="")]
    next_node: Annotated[str, Field(default="")]