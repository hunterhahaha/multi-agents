from typing import Annotated, List
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class StateMessages(BaseModel):
    """
    StateMessages 的 Docstring
    参数：
        messages: 消息列表，用于存储对话历史记录。
        code: 代码，用于存储生成的代码。
        code_result: 代码运行结果，用于存储运行生成的代码后的结果。
        answer: 回答，用于存储生成的回答。
    """
    messages: Annotated[List[BaseMessage], add_messages]
    code: Annotated[str, Field(default="")]
    answer: Annotated[str, Field(default="")]