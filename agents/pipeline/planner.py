"""
planner.py — 规划层

职责：
    理解用户任务，结合当前可用 Worker 列表，输出结构化的 ExecutionPlan。
    若 Reviewer 封驳，接收 review_result.feedback 后修改 Plan 重新输出。

读取 State：
    - question       : 用户原始任务
    - review_result  : Reviewer 的审核意见（仅重规划时非空）

写入 State：
    - execution_plan : 生成的执行方案
    - next_node      : 固定写 "reviewer"

不得：
    - 调用任何 Worker 或工具
    - 修改 question、messages、task_history
    - 做任何执行操作，只做规划

输出格式（结构化 JSON，必须严格遵守）：
    {
        "objective": "一句话描述本次任务目标",
        "steps": [
            {
                "step_id": "step_1",
                "description": "具体任务描述，直接传给 Worker 执行",
                "assigned_worker": "worker_name（必须是可用 Worker 列表中的名称）",
                "dependencies": []   // 无依赖填空列表；有依赖填前置 step_id 列表
            }
        ]
    }

规划原则：
    1. 能并行的步骤不要串行（dependencies 为空即可并行）
    2. assigned_worker 必须从「可用 Worker 列表」中选择，禁止杜撰
    3. description 要足够具体，Worker 不需要再看 question 也能执行
    4. 步骤数量以够用为准，不要过度拆分
"""

import json
from agents.state import StateMessages, ExecutionPlan
from agents.worker_registry import WorkerRegistry

# TODO: 替换为实际模型
# from Models.Deepseek import chat_model

PLANNER_SYSTEM_PROMPT = """
你是一个任务规划专家。你的职责是将用户任务拆解为结构化的执行方案。

可用 Worker 列表：
{worker_descriptions}

输出要求：
- 严格输出 JSON，不要有任何额外文字
- step_id 格式：step_1, step_2, ...
- assigned_worker 必须是上方列表中的名称
- 能并行执行的步骤请将 dependencies 设为空列表 []
- description 要具体到 Worker 无需参考原始问题也能独立执行

输出格式：
{{
    "objective": "...",
    "steps": [
        {{"step_id": "step_1", "description": "...", "assigned_worker": "...", "dependencies": []}}
    ]
}}
"""


def _build_prompt(state: StateMessages) -> str:
    """根据是否是重规划，拼接不同的用户 prompt。"""
    base = f"任务：{state['question']}"
    review = state.get("review_result")
    if review and not review["approved"] and review["feedback"]:
        base += f"\n\n上一版方案被审核退回，原因：{review['feedback']}\n请根据以上意见修改方案。"
    return base


def planner_node(state: StateMessages) -> dict:
    worker_descriptions = WorkerRegistry.get_supervisor_choices()
    system_prompt = PLANNER_SYSTEM_PROMPT.format(worker_descriptions=worker_descriptions)

    # TODO: 替换为实际 LLM 调用
    # from langchain_core.messages import SystemMessage, HumanMessage
    # model = chat_model.build()
    # response = model.invoke([
    #     SystemMessage(system_prompt),
    #     HumanMessage(_build_prompt(state)),
    # ])
    # plan: ExecutionPlan = json.loads(response.content)

    # 占位：空 Plan，防止后续节点崩溃
    plan: ExecutionPlan = {
        "objective": state.get("question") or "",
        "steps": [],
    }

    return {
        "execution_plan": plan,
        "next_node": "reviewer",
    }
