from langgraph.graph import StateGraph, START, END
from Cores.States.structs import GraphState 
from three_departments.dispatcher import dispatcher
from three_departments.planner import planner

graph = StateGraph(GraphState)

graph.add_node("dispatch", dispatcher)
graph.add_node("plan", planner)

graph.add_edge(START, "dispatch")
graph.add_conditional_edges(
    "dispatch",
    lambda state: state["intent_judge"],
    {
        "chat": END,
        "task": "plan"
    }
)
graph.add_edge("plan", END)

graph = graph.compile()

if __name__ == "__main__":
    input = "你好"
    result = graph.invoke({"user_input": input})
    print(result)