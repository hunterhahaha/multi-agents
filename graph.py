from langgraph.graph import StateGraph, START, END
from Cores.States.structs import GraphState 
from three_departments.dispatcher import dispatcher
from three_departments.planner import planner
from three_departments.reviewer import reviewer

graph = StateGraph(GraphState)

graph.add_node("dispatch", dispatcher)
graph.add_node("plan", planner)
graph.add_node("review", reviewer)

graph.add_edge(START, "dispatch")
graph.add_conditional_edges(
    "dispatch",
    lambda state: state["intent_judge"],
    {
        "chat": END,
        "task": "plan"
    }
)
graph.add_edge("plan", "review")
graph.add_conditional_edges(
    "review",
    lambda state: state["is_return"],
    {
        "True": "plan",
        "False": END
    }
)

graph = graph.compile()

if __name__ == "__main__":
    input = "请帮我写一个简单的待办事项应用，包含添加任务、删除任务和查看任务列表的功能。"
    result = graph.invoke(
        {
            "user_input": input, 
            "return_count": 0,
            "planner_messages": [],
            "reviewer_messages": []
        }
    )
    print(result)