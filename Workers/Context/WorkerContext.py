"""管理 Worker 的上下文"""

from abc import ABC, abstractmethod

class WorkerContext:
    """
    管理 Worker 的上下文
    """
    def __init__(self):
        self.history: list = [] # 存放本轮执行的历史信息
        self.task_result: str = "" # 存放本轮执行的结果（报错时存报错信息）
        self.task_success: bool = False # 存放本轮执行是否成功