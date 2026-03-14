from typing import Optional, Literal, TypedDict, Annotated, NotRequired
from collections import deque
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from enum import Enum
from langgraph.graph import add_messages

MAX_RETURN_COUNT = 5 # Reviewer 打回计划的最大次数上限

# TaskStatus，任务状态枚举
class TaskStatus(str, Enum):
    PENDING = "pending" # 等待前置任务完成
    READY = "ready" # 前置任务已完成，等待执行
    RUNNING = "running" # 正在执行
    DONE = "done" # 已完成
    FAILURE = "failure" # 执行失败

# WORKER_STATUS，员工最终状态枚举
class WorkerStatus(str, Enum):
    DONE = "done" # 已完成
    FAILURE = "failure" # 执行失败

# WorkerName，员工名称枚举
class WorkerName(str, Enum):
    """后续陆续添加进来"""
    pass

# TaskNode，任务节点描述
class TaskNode(BaseModel):
    task_id: str = Field(description="任务ID")
    worker: Optional[WorkerName] = Field(default=None, description="员工名称")
    description: str = Field(description="任务描述")
    dependencies: list[str] = Field(default_factory=list, description="前置任务列表，列表中用 task_id 标识")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    input_from: list[str] = Field(default_factory=list, description="输入来源，列表中用 task_id 标识，表示该任务的输入需要哪些任务的输出")
    input_data: list[str] = Field(default_factory=list, description="任务输入数据，通常是前置任务的输出结果的聚合列表")
    output: Optional[str] = Field(default=None, description="任务输出")

# DAG，规划表
class DAG(BaseModel):
    nodes: dict[str, TaskNode] = Field(default_factory=dict, description="DAG图的节点集合，task_id -> TaskNode")

    def verify_no_cycle(self) -> bool:
        """
        检测 DAG 是否为合法的无环图。
        返回 True 表示无环且依赖关系合法；False 表示存在环或依赖非法。
        """
        # 空图默认合法
        if not self.nodes:
            return True

        # 邻接表
        adj: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        # 入度表
        indegree: dict[str, int] = {node_id: 0 for node_id in self.nodes}

        # 构建邻接表与入度表
        for node_id, node in self.nodes.items():
            # key 与 task_id 不同时视为非法
            if node.task_id != node_id:
                return False

            for dep_node_id in node.dependencies:
                # 依赖不存在时视为非法
                if dep_node_id not in self.nodes:
                    return False
                # 存在自环时视为非法
                if dep_node_id == node_id:
                    return False

                adj[dep_node_id].append(node_id)
                indegree[node_id] += 1

        # Kahn，拓扑排序
        queue = deque([node_id for node_id, degree in indegree.items() if degree == 0])
        visited_count = 0

        while queue:
            current_node_id = queue.popleft()
            visited_count += 1
            for next_node_id in adj[current_node_id]:
                indegree[next_node_id] -= 1
                if indegree[next_node_id] == 0:
                    queue.append(next_node_id)

        return visited_count == len(self.nodes)

# WorkerOutput，员工最终输出
class WorkerOutput(TypedDict):
    task_id: str = Field(description="任务ID")
    worker: Optional[WorkerName] = Field(default=None, description="员工名称")
    output: Optional[str] = Field(default=None, description="员工执行结果")
    error: Optional[str] = Field(default=None, description="员工执行错误信息")
    status: WorkerStatus = Field(default=WorkerStatus.DONE, description="员工执行状态")

# Dispatcher，分拣者状态
class DispatcherStruct(TypedDict):
    user_input: str
    intent_judge: Optional[Literal["chat", "task"]] = Field(default=None, description="用户意图判断，chat 或 task")
    messages_history: list[BaseMessage] = Field(default_factory=list, description="存储多轮对话的消息历史记录")
    chat_reply: Optional[str] = Field(default=None, description="intent=chat 时有值")
    task: Optional[str] = Field(default=None, description="intent=task 时有值")

# Planner，规划者状态
class PlannerStruct(TypedDict):
    task: str
    plan: Optional[DAG] = Field(default=None, description="任务计划，DAG图，节点为任务，边为任务依赖关系")
    review: Optional[str] = Field(default=None, description="Reviewer 对计划的评审意见")

# Reviewer，审核者状态
class ReviewerStruct(TypedDict):
    review: Optional[str] = Field(default=None, description="Reviewer 对计划的评审意见")
    is_return: bool = Field(default=False, description="Reviewer 是否打回计划")
    return_count: int = Field(default=0, description="Reviewer 打回计划的次数，有最大上限，在实际程序中进行检测，暂定5次", )

# Scheduler，调度者状态
class SchedulerStruct(TypedDict):
    reviewed_plan: Optional[DAG] = Field(default=None, description="经过 Reviewer 审核通过的计划")
    workers_output: list[WorkerOutput] = Field(default_factory=list, description="每个 worker 执行完成后的结果的聚合列表")

# Reporter，报告者状态
class ReporterStruct(TypedDict):
    workers_output: list[WorkerOutput] = Field(default_factory=list, description="每个 worker 执行完成后的结果的聚合列表")
    report: Optional[str] = Field(default=None, description="最终的报告内容")

# GraphState，“三省” Graph 的状态，统一管理所有“三省”角色
class GraphState(TypedDict):
    # 长期记忆，多轮对话中保留
    messages_history: Annotated[list[BaseMessage], add_messages]
    # 任务级记忆，任务结束后销毁
    intent_judge: NotRequired[Literal["chat", "task"]]
    chat_reply: NotRequired[str]
    task: NotRequired[str]
    plan: NotRequired[DAG]
    review: NotRequired[str]
    is_return: NotRequired[bool]
    return_count: NotRequired[int]
    reviewed_plan: NotRequired[DAG]
    workers_output: NotRequired[list[WorkerOutput]]
    report: NotRequired[str]
