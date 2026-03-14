"""
state.py — 系统状态契约

本文件是整个系统的数据契约，所有节点通过读写同一个 StateMessages 通信。
修改本文件会影响所有节点，改动前请确认所有相关节点的兼容性。

数据结构分层：
  TaskRecord       — Worker 执行一次任务后的标准化汇报（执行层产物）
  ExecutionStep    — Plan 中的单个步骤定义（规划层产物的组成单元）
  ExecutionPlan    — Planner 输出的完整执行方案（规划层产物）
  ReviewResult     — Reviewer 对 Plan 的审核结论（审核层产物）
  StateMessages    — 全局共享状态，五层结构
"""

from __future__ import annotations
from typing import Annotated, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from operator import add


# ─────────────────────────────────────────────
# 执行层：Worker 的汇报格式
# ─────────────────────────────────────────────

class TaskRecord(TypedDict):
    """
    Worker 完成一次步骤后的标准化汇报。
    由 BaseWorker.run() 生成，追加到 state["task_history"]。

    字段：
        step_id      : 对应 ExecutionStep.step_id，供 Scheduler 追踪进度
                       Dispatcher 直接回复闲聊时填 "chat"
        worker       : 执行者名称，对应 WorkerRegistry 中注册的 name
        task         : Scheduler 下达的任务描述原文
        task_result  : Worker 的输出内容
        task_success : Worker 自评是否成功完成任务；
                       False 时 Scheduler 会跳过依赖此步骤的后续步骤
    """
    step_id: str
    worker: str
    task: str
    task_result: str
    task_success: bool


# ─────────────────────────────────────────────
# 规划层：Planner 的输出格式
# ─────────────────────────────────────────────

class ExecutionStep(TypedDict):
    """
    ExecutionPlan 中的单个执行步骤。

    字段：
        step_id         : 唯一标识，格式为 "step_1"、"step_2"...
                          Scheduler 和 TaskRecord 通过此字段互相关联
        description     : 任务描述，Scheduler 原文传给对应 Worker 作为 task
        assigned_worker : 负责执行的 Worker 名，必须在 WorkerRegistry 中已注册
        dependencies    : 前置步骤的 step_id 列表
                          空列表 [] 表示无依赖，可立即执行
                          非空时，所有前置步骤的 task_success 必须为 True 才派发
    """
    step_id: str
    description: str
    assigned_worker: str
    dependencies: List[str]


class ExecutionPlan(TypedDict):
    """
    Planner 输出的完整执行方案。
    经 Reviewer 准奏后由 Scheduler 消费，此后视为不可变。

    字段：
        objective : 本次任务目标，一句话概括，Reporter 汇总时引用
        steps     : 步骤列表

    关键约束：
        - Plan 一经 Reviewer 通过即不再修改
        - 步骤状态不存储在 Plan 里，由 task_history 追踪
        - Scheduler 通过对比 steps 与 task_history 推断当前进度
        - steps 中 assigned_worker 的值必须都是已注册的 Worker 名
    """
    objective: str
    steps: List[ExecutionStep]


# ─────────────────────────────────────────────
# 审核层：Reviewer 的输出格式
# ─────────────────────────────────────────────

class ReviewResult(TypedDict):
    """
    Reviewer 对 ExecutionPlan 的审核结论。
    每次审核覆盖写入 state["review_result"]。

    字段：
        approved    : True 表示准奏，流程进入 Scheduler
                      False 表示封驳，流程退回 Planner 重规划
        feedback    : 审核意见
                      approved=True 时可为空字符串
                      approved=False 时必须说明具体原因，Planner 据此修改
        retry_count : Planner-Reviewer 循环次数，由 Reviewer 负责递增
                      达到上限时 Reviewer 应强制将 approved 设为 True，防止死循环
                      上限常量定义在 reviewer.py: MAX_REVIEW_RETRIES = 2
    """
    approved: bool
    feedback: str
    retry_count: int


# ─────────────────────────────────────────────
# 全局状态
# ─────────────────────────────────────────────

class StateMessages(TypedDict):
    """
    系统全局共享状态，所有节点读写同一份实例。

    写入权限约定（各层只写自己负责的字段，只读其他层）：
        用户层    ← 系统入口写入，其余节点只读
        规划层    ← Planner 写入
        审核层    ← Reviewer 写入
        调度层    ← Dispatcher / Reviewer / Scheduler 写入 next_node
                    Scheduler 写入 task / current_step_id
        执行层    ← Worker 追加，只追加不修改（Annotated add）
        输出层    ← Reporter 写入
    """

    # ── 用户层 ──────────────────────────────────────────────────
    question: str | None
    """用户的原始输入，全程不修改"""

    messages: Annotated[List[BaseMessage], add]
    """多轮对话历史；仅 Dispatcher 处理闲聊时追加 AIMessage"""

    # ── 规划层 ──────────────────────────────────────────────────
    execution_plan: ExecutionPlan | None
    """Planner 输出的执行方案；Reviewer 通过后不再修改"""

    # ── 审核层 ──────────────────────────────────────────────────
    review_result: ReviewResult | None
    """Reviewer 的最新审核结论；每次审核覆盖写入"""

    # ── 调度层 ──────────────────────────────────────────────────
    current_step_id: str | None
    """Scheduler 当前派发的步骤 ID；Worker 将其写入 TaskRecord.step_id"""

    task: str | None
    """Scheduler 下达给当前 Worker 的任务描述（来自 ExecutionStep.description）"""

    next_node: str | None
    """下一个执行的节点名；由 Dispatcher / Reviewer / Scheduler 写入，graph 路由读取"""

    # ── 执行层 ──────────────────────────────────────────────────
    task_history: Annotated[List[TaskRecord], add]
    """所有已完成步骤的执行记录；只追加，不修改历史条目"""

    # ── 输出层 ──────────────────────────────────────────────────
    answer: str | None
    """Reporter 写入的最终回答，输出给用户"""
