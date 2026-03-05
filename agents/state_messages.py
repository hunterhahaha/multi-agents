from typing import Annotated, List, TypedDict
from pydantic import Field
from langchain_core.messages import BaseMessage
from operator import add

class TaskRecord(TypedDict):
    worker: str = "" # 执行任务的员工
    task: str = "" # 员工的任务
    task_result: str = "" # 任务的结果
    task_success: bool = False # 任务是否成功完成

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
    # 用户层
    question: str | None # 用户原始问题
    messages: Annotated[List[BaseMessage], add] | None # 历史对话列表

    # 调度层
    task: str | None # supervisor 交代给员工的任务
    next_node: str | None # 下一个要执行的员工节点

    # 员工返回层
    task_history: Annotated[List[TaskRecord], add] | None # 存储任务的执行记录

    # 最终输出层
    answer: str | None # 输出给用户的回答
