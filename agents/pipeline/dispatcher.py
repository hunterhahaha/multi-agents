"""
dispatcher.py — 分拣层

职责：
    判断用户输入是「闲聊」还是「任务」。
    - 闲聊：直接生成回复，写入 messages，流程到 END
    - 任务：写入 question，流程进入 Planner

读取 State：
    - question  : 用户原始输入
    - messages  : 历史对话（提供上下文）

写入 State：
    - next_node : "planner"（任务）或 "end"（闲聊）
    - messages  : 仅闲聊时追加 AIMessage 作为回复

不得：
    - 修改 question
    - 生成或修改 execution_plan
    - 调用任何 Worker

判断标准（prompt 中明确）：
    任务 = 需要多步骤分析、调研、编写代码、生成报告等有明确产出的请求
    闲聊 = 问候、闲聊、简单事实查询、对上一轮结果的追问
"""

from langchain_core.messages import AIMessage
from agents.state import StateMessages

# TODO: 替换为实际模型
# from Models.Deepseek import chat_model

# 判断阈值：当 LLM 返回此标记时视为任务
_TASK_SIGNAL = "__TASK__"
_CHAT_SIGNAL = "__CHAT__"

DISPATCHER_PROMPT = """
你是一个消息分拣员，只做一件事：判断用户的输入是「闲聊」还是「任务」。

判断规则：
- 任务：需要多步骤处理的请求，例如：调研、写代码、生成报告、数据分析、制定方案
- 闲聊：问候、日常对话、简单事实问答、对上一轮回复的简短追问

输出格式（严格遵守，只输出以下两种之一）：
- 如果是任务：输出 __TASK__
- 如果是闲聊：输出 __CHAT__\n<闲聊回复内容>

示例：
用户：「帮我分析一下竞品市场」→ __TASK__
用户：「你好！」→ __CHAT__\n你好！有什么可以帮你的吗？
用户：「上面那个结果可以再详细一点吗」→ __TASK__
"""


def dispatcher_node(state: StateMessages) -> dict:
    # TODO: 用 chat_model 替换此处的占位逻辑
    # model = chat_model.build()
    # messages = [SystemMessage(DISPATCHER_PROMPT), HumanMessage(state["question"])]
    # response = model.invoke(messages)
    # output = response.content.strip()

    # 占位：默认所有输入都视为任务
    output = _TASK_SIGNAL

    if output.startswith(_TASK_SIGNAL):
        return {"next_node": "planner"}
    else:
        # 截取 __CHAT__\n 后面的回复内容
        reply = output.replace(_CHAT_SIGNAL, "", 1).strip()
        return {
            "next_node": "end",
            "messages": [AIMessage(content=reply)],
            "answer": reply,
        }


def dispatcher_router(state: StateMessages) -> str:
    """graph.py 中 add_conditional_edges 使用的路由函数。"""
    return state["next_node"] or "planner"
