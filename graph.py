from langgraph.graph import StateGraph, START, END
from agents.state_messages import StateMessages
from agents.role1 import role_1_node
from agents.role2 import role_2_node
from agents.role3 import role_3_node
from agents.router_1 import router_1_node, intent_judge

graph = StateGraph(StateMessages)
graph.add_node("role_1", role_1_node)
graph.add_node("role_2", role_2_node)
graph.add_node("role_3", role_3_node)
graph.add_node("router_1", router_1_node)
graph.add_node("intent_judge", intent_judge)

# 并行角色一和意图判断
graph.add_edge(START, "role_1")
graph.add_edge(START, "intent_judge")
# 合并，并决策路径
graph.add_edge("role_1", "router_1")
graph.add_edge("intent_judge", "router_1")
graph.add_conditional_edges(
    "router_1",
    lambda state: state.next_node,
    {
        "role_2": "role_2",
        "END": END,
    },
)
graph.add_edge("role_2", "role_3")
graph.add_edge("role_3", END)
graph = graph.compile()