from Cores.Models.model import chat_model
from Cores.States.structs import ReviewerStruct
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from typing import Literal
from Cores.Prompts.reviewer import reviewer_prompt
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.tools import tool
from Cores.Agents.Base import BaseAegnt

class ReviewResult(BaseModel):
        is_return: Literal["False", "True"]
        review: str

@tool(description="结构化输出工具，必须调用该工具来结束整个任务。")
def structured_output_tool(result: ReviewResult) -> ReviewResult:
    return result

reviewer = StateGraph(ReviewerStruct)

def review(state: ReviewerStruct) -> ReviewerStruct:
    """
    根据 Planner 生成的 DAG 执行计划，进行审核，判断是否合理，并给出合理性的反馈意见。
    """

    if state["reviewer_messages"] == []:
        state["reviewer_messages"].append(SystemMessage(content=reviewer_prompt))
    
    state["reviewer_messages"].append(HumanMessage(content=state["plan"].model_dump_json()))

    class ReviewResult(BaseModel):
        is_return: Literal["False", "True"]
        review: str

    review_agent = BaseAegnt(model=chat_model, tools=[structured_output_tool])

    result = review_agent.invoke(state["reviewer_messages"])

    if result.is_return == "True" and state["return_count"] == 5:
        raise ValueError("Reviewer 已打回5次，Planner 仍未能生成合理的计划，请检查 Planner 的设计或实现是否存在问题。")
    return {
        "review": result.review,
        "is_return": result.is_return,
        "return_count": state["return_count"] + (0 if result.is_return == "False" else 1),
        "reviewer_messages": state["reviewer_messages"] + [AIMessage(content=result.review)]
    }

reviewer.add_node(review)

reviewer.add_edge(START, "review")
reviewer.add_edge("review", END)
reviewer = reviewer.compile()