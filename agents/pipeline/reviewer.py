"""
reviewer.py — 审核层

职责：
    对 Planner 输出的 ExecutionPlan 进行质量审核。
    审核通过（准奏）：流程进入 Scheduler。
    审核不通过（封驳）：流程退回 Planner 重规划，并提供具体修改意见。

读取 State：
    - execution_plan  : 待审核的方案
    - review_result   : 上一轮审核结果（用于获取 retry_count）
    - question        : 原始任务（判断 Plan 是否对题）

写入 State：
    - review_result   : 本次审核结论（覆盖写入）
    - next_node       : "scheduler"（准奏）或 "planner"（封驳）

不得：
    - 修改 execution_plan
    - 调用任何 Worker 或工具
    - 执行任何任务

审核标准（prompt 中明确）：
    1. 目标是否与用户任务对应？
    2. 步骤是否完整？有无明显遗漏？
    3. assigned_worker 是否与步骤类型匹配？
    4. 依赖关系是否合理？有无循环依赖？
    5. 步骤描述是否足够具体？Worker 能否独立执行？

防死循环：
    retry_count >= MAX_REVIEW_RETRIES 时强制 approved=True
"""

from agents.state import StateMessages, ReviewResult

# TODO: 替换为实际模型
# from Models.Deepseek import chat_model

MAX_REVIEW_RETRIES = 2

REVIEWER_SYSTEM_PROMPT = """
你是一个方案审核专家（门下省）。你的职责是审核任务执行方案的质量。

审核标准：
1. 方案目标是否与用户任务对应？
2. 步骤是否完整，有无明显遗漏的关键步骤？
3. 每个步骤的 assigned_worker 是否与任务类型匹配？
4. 依赖关系是否合理？是否存在循环依赖？
5. 步骤描述是否具体，Worker 是否能够独立执行而无需查看原始问题？

输出要求：
- 严格输出 JSON，不要有任何额外文字
- 如果方案合格：{{"approved": true, "feedback": ""}}
- 如果方案不合格：{{"approved": false, "feedback": "具体说明哪些地方需要修改"}}
"""


def reviewer_node(state: StateMessages) -> dict:
    plan = state.get("execution_plan")
    prev = state.get("review_result")
    retry_count = (prev["retry_count"] + 1) if prev else 0

    # 防死循环：超过重试上限强制放行
    if retry_count >= MAX_REVIEW_RETRIES:
        result: ReviewResult = {
            "approved": True,
            "feedback": f"已达最大重试次数 ({MAX_REVIEW_RETRIES})，强制放行。",
            "retry_count": retry_count,
        }
        return {
            "review_result": result,
            "next_node": "scheduler",
        }

    # TODO: 替换为实际 LLM 调用
    # import json
    # from langchain_core.messages import SystemMessage, HumanMessage
    # model = chat_model.build()
    # plan_text = json.dumps(plan, ensure_ascii=False, indent=2)
    # response = model.invoke([
    #     SystemMessage(REVIEWER_SYSTEM_PROMPT),
    #     HumanMessage(f"原始任务：{state['question']}\n\n待审核方案：\n{plan_text}"),
    # ])
    # raw = json.loads(response.content)

    # 占位：默认全部准奏
    raw = {"approved": True, "feedback": ""}

    result: ReviewResult = {
        "approved": raw["approved"],
        "feedback": raw.get("feedback", ""),
        "retry_count": retry_count,
    }

    return {
        "review_result": result,
        "next_node": "scheduler" if result["approved"] else "planner",
    }


def reviewer_router(state: StateMessages) -> str:
    """graph.py 中 add_conditional_edges 使用的路由函数。"""
    return state["next_node"] or "scheduler"
