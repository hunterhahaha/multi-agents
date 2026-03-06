""""""
from abc import ABC, abstractmethod
from .Context.WorkerContext import WorkerContext
from langchain.messages import SystemMessage, HumanMessage, ToolMessage


class BaseWorker(ABC):
    name: str # worker 名称
    description: str # worker 描述
    prompt: str # worker 的 prompt 模板
    tools: list = [] # worker 配置的工具列表
    model_config = ... # worker 配置的模型参数

    def create_context(self, state) -> WorkerContext:
        """为 worker 创建上下文"""
        return WorkerContext()
    
    def build_input(self, state, context: WorkerContext) -> str:
        """构造输入"""
        return [
            SystemMessage(
                content=self.prompt
            ), 
            *context.history,
            HumanMessage(
                content=state["task"]
            ),
        ]
    
    def on_tool_reslult(self, tool_call, result, context: WorkerContext):
        """处理工具调用结果"""
        context.history.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
        )