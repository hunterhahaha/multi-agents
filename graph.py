from langgraph.graph import StateGraph, START, END
from agents.state_messages import StateMessages
from agents.role1 import role_1_node
from agents.role2 import role_2_node
from agents.role3 import role_3_node
from agents.chat_node import chat_node
from agents.intent_node import intent_node
from agents.Supervisor_agent import supervisor_node

from langgraph.checkpoint.memory import InMemorySaver

checkpoint = InMemorySaver()

graph = StateGraph(StateMessages)
graph.add_node("role_1", role_1_node)
graph.add_node("role_2", role_2_node)
graph.add_node("role_3", role_3_node)
graph.add_node("chat", chat_node)
graph.add_node("supervisor", supervisor_node)

graph.add_edge(START, "supervisor")

# 任务调度器
graph.add_conditional_edges(
    "supervisor",
    lambda state: state["next_node"],
    {
        "role_1": "role_1",
        "chat": "chat",
        "END": END, 
    },
)

# 路径一
graph.add_edge("role_1", "role_2")
graph.add_edge("role_2", "role_3")

# 路径二
graph.add_edge("chat", "supervisor")

# 沙盒代码执行异常反馈环
graph.add_conditional_edges(
    "role_3",
    lambda state: state["next_node"],
    {
        "role_2": "role_2",
        END: "supervisor",
    },
)

graph = graph.compile(checkpointer=checkpoint)