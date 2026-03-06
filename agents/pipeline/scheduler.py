"""
scheduler.py — 调度层

职责：
    读取 ExecutionPlan 和 task_history，找出下一个可执行的步骤并派发。
    所有步骤完成后，路由到 Reporter。

读取 State：
    - execution_plan  : 完整执行方案（不可变）
    - task_history    : 所有已完成步骤的记录

写入 State：
    - current_step_id : 当前派发的步骤 ID（完成后清空）
    - task            : 当前步骤的描述，直接传给 Worker
    - next_node       : Worker 名称 或 "reporter"

不得：
    - 修改 execution_plan
    - 调用 LLM（纯逻辑节点）
    - 修改 task_history

调度算法：
    1. 从 task_history 提取 completed_ids（task_success=True 的 step_id）
    2. 从 task_history 提取 attempted_ids（所有出现过的 step_id）
    3. 遍历 execution_plan.steps，找第一个满足条件的步骤：
       - 未在 attempted_ids 中（未尝试过）
       - 所有 dependencies 都在 completed_ids 中（前置条件满足）
    4. 找到 → 派发该步骤；未找到 → 路由到 reporter

依赖失败处理：
    当某步骤的依赖步骤执行失败（task_success=False）时，
    该步骤的依赖条件永远无法满足，会被跳过。
    Reporter 将在汇总时处理部分失败的情况。
    （后续可扩展重试机制：在 task_history 中允许同一 step_id 出现多次）
"""

from agents.state import StateMessages


def scheduler_node(state: StateMessages) -> dict:
    plan = state.get("execution_plan")
    history = state.get("task_history") or []

    # Plan 不存在（理论上不应发生，防御性处理）
    if not plan or not plan.get("steps"):
        return {
            "current_step_id": None,
            "task": None,
            "next_node": "reporter",
        }

    # 从 task_history 提取进度
    completed_ids = {r["step_id"] for r in history if r["task_success"]}
    attempted_ids = {r["step_id"] for r in history}

    # 找下一个可执行步骤
    for step in plan["steps"]:
        # 跳过已尝试的步骤（无论成功失败）
        if step["step_id"] in attempted_ids:
            continue
        # 检查所有前置依赖是否已完成
        if all(dep in completed_ids for dep in step["dependencies"]):
            return {
                "current_step_id": step["step_id"],
                "task": step["description"],
                "next_node": step["assigned_worker"],
            }

    # 所有步骤都已尝试（或无法满足依赖），进入 Reporter
    return {
        "current_step_id": None,
        "task": None,
        "next_node": "reporter",
    }


def scheduler_router(state: StateMessages) -> str:
    """graph.py 中 add_conditional_edges 使用的路由函数。"""
    return state["next_node"] or "reporter"
