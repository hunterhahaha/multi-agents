"""
reporter.py — 输出层

职责：
    汇总所有步骤的执行结果，生成面向用户的最终回答。
    是流程的最后一个节点，输出后进入 END。

读取 State：
    - question        : 用户原始任务（回答需对题）
    - execution_plan  : 任务目标和步骤定义（了解整体目标）
    - task_history    : 所有步骤的执行记录（核心输入）

写入 State：
    - answer          : 最终回答，输出给用户

不得：
    - 调用任何 Worker 或工具
    - 修改 task_history 或 execution_plan
    - 发起任何新的执行

汇总原则（prompt 中明确）：
    1. 先说结论，再说过程
    2. 所有步骤成功 → 完整汇总结果
    3. 部分步骤失败 → 说明哪些完成、哪些失败及原因，给出可用的部分结果
    4. 全部失败 → 说明失败原因，给出建议
    5. 语言简洁，不重复 task_history 的原始内容，做提炼和整合
"""

import json
from agents.state import StateMessages

# TODO: 替换为实际模型
# from Models.Deepseek import chat_model

REPORTER_SYSTEM_PROMPT = """
你是一个报告撰写专家。你的职责是将多个执行步骤的结果整合为一份面向用户的清晰回答。

汇总原则：
1. 开门见山，先给出结论或核心结果
2. 按逻辑顺序整合各步骤结果，不要逐条罗列原始输出
3. 如有步骤失败，明确说明哪些完成、哪些失败，以及失败原因
4. 语言简洁，避免冗余，聚焦用户真正关心的内容
5. 如果结果包含代码或数据，保留原始格式
"""


def reporter_node(state: StateMessages) -> dict:
    plan = state.get("execution_plan")
    history = state.get("task_history") or []
    question = state.get("question") or ""

    # 构建汇总上下文
    objective = plan["objective"] if plan else question
    results_text = "\n".join(
        f"[{r['step_id']}] {r['worker']}: {'✓' if r['task_success'] else '✗'} {r['task_result']}"
        for r in history
        if r["step_id"] != "chat"  # 排除闲聊记录
    )

    # TODO: 替换为实际 LLM 调用
    # from langchain_core.messages import SystemMessage, HumanMessage
    # model = chat_model.build()
    # response = model.invoke([
    #     SystemMessage(REPORTER_SYSTEM_PROMPT),
    #     HumanMessage(
    #         f"用户任务：{question}\n"
    #         f"任务目标：{objective}\n\n"
    #         f"执行结果：\n{results_text}"
    #     ),
    # ])
    # answer = response.content

    # 占位：直接拼接结果
    answer = f"任务「{objective}」执行完成。\n\n{results_text}" if results_text else "任务已完成，无执行记录。"

    return {"answer": answer}
