from Cores.Models.model import reasoner_model
from Cores.States.structs import PlannerStruct, DAG
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.tools import tool
from Cores.Agents.Base import BaseAegnt
from langchain.tools import tool
from Cores.Prompts.planner import planner_prompt

@tool(description="结构化输出工具，必须调用该工具来结束整个任务。")
def structured_output_tool(result: DAG) -> DAG:
    return result

planner = StateGraph(PlannerStruct)

def plan(state: PlannerStruct) -> PlannerStruct:
    """
    根据用户输入的任务描述，生成一个结构化的 DAG 执行计划
    """

    if state["planner_messages"] == []:
        state["planner_messages"].append(SystemMessage(content=planner_prompt))
        state["planner_messages"].append(HumanMessage(content=f"用户输入的任务描述是：{state['task']}"))

    if state.get("review"):
        state["planner_messages"].append(HumanMessage(content=f"你之前的plan的审核意见是：{state['review']}"))
        state["planner_messages"].append(HumanMessage(content=f"你之前的plan是：{state['plan'].model_dump_json()}"))

    plan_agent = BaseAegnt(model=reasoner_model, tools=[structured_output_tool])

    for attemp in range(3):
        result = plan_agent.invoke(state["planner_messages"])

        if result.verify_no_cycle():
            return {
                "plan": result,
                "planner_messages": state["planner_messages"] + [AIMessage(content=result.model_dump_json())]
            }
        else:
            state["planner_messages"].append(AIMessage(content=result.model_dump_json()))
            state["planner_messages"].append(HumanMessage(content="你生成的 DAG 存在循环依赖，请重新规划，确保无环。"))

    raise ValueError("Planner 多次生成无效 DAG")

planner.add_node(plan)

planner.add_edge(START, "plan")
planner.add_edge("plan", END)
planner = planner.compile()