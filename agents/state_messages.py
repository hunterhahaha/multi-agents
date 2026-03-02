from typing import Annotated, List, TypedDict
from pydantic import Field
from langchain_core.messages import BaseMessage
from operator import add

class StateMessages(TypedDict):
    """
    参数：
        question: 问题，用于存储用户的原始问题。
        messages: 消息列表，用于存储对话历史记录。

        code: 代码，用于存储生成的代码。
        code_result: 代码运行结果，用于存储运行生成的代码后的结果。
        code_error: 代码运行错误，用于存储运行生成的代码后的错误信息。
        retry_count: 重试次数，用于存储重试运行代码的次数。

        answer: 回答，用于存储生成的回答。
        next_node: 下一个节点，用于存储下一个要执行的节点。
        use_reasoner: 是否需要使用推理模型。
    """
    question: Annotated[str, Field(default="")]
    messages: Annotated[List[BaseMessage], add]

    code: Annotated[str, Field(default="")]
    code_result: Annotated[str, Field(default="")]
    code_error: Annotated[str, Field(default="")]
    retry_count: Annotated[int, Field(default=0)]

    answer: Annotated[str, Field(default="")]
    next_node: Annotated[str, Field(default="")]
    use_reasoner: Annotated[bool, Field(default=False)]