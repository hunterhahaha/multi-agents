from Cores.Models.model import chat_model
from Cores.States.structs import PlannerStruct, DAG
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import Literal
from Cores.Prompts.dispatcher import dispatcher_prompt
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

planner = StateGraph(PlannerStruct)

def plan(state: PlannerStruct) -> PlannerStruct:
    """
    根据用户输入的任务描述，生成一个结构化的 DAG 执行计划
    """
    from Cores.Prompts.planner import planner_prompt

    messages = [
        SystemMessage(content=planner_prompt),
        HumanMessage(content=state["task"])
    ]

    plan_llm = chat_model.with_structured_output(DAG)

    for attemp in range(3):
        result = plan_llm.invoke(messages)

        if result.verify_no_cycle():
            return {
                "plan": result
            }
        else:
            messages.append(AIMessage(content=result.model_dump_json()))
            messages.append(HumanMessage(content="你生成的 DAG 存在循环依赖，请重新规划，确保无环。"))

    raise ValueError("Planner 多次生成无效 DAG")

planner.add_node(plan)

planner.add_edge(START, "plan")
planner.add_edge("plan", END)
planner = planner.compile()

if __name__ == "__main__":
    input = "生成一个愤怒的小鸟的网页游戏"
    result = planner.run({"task": input})
    print(result)