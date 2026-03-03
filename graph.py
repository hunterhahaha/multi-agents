from langgraph.graph import StateGraph, START, END
from agents.state_messages import StateMessages
from agents.planner import planner_node
from agents.coder import coder_node
from agents.executor import executor_node
from agents.chatter import chat_node
from agents.supervisor import supervisor_node
from agents.researcher import researcher_node
from langgraph.checkpoint.memory import InMemorySaver

checkpoint = InMemorySaver()

graph = StateGraph(StateMessages)
graph.add_node("planner", planner_node)
graph.add_node("coder", coder_node)
graph.add_node("executor", executor_node)
graph.add_node("chatter", chat_node)
graph.add_node("supervisor", supervisor_node)
graph.add_node("researcher", researcher_node)

graph.add_edge(START, "supervisor")

# 任务调度器
graph.add_conditional_edges(
    "supervisor",
    lambda state: state["next_node"],
    {
        "planner": "planner",
        "researcher": "researcher",
        "chatter": "chatter",
        "END": END, 
    },
)

# 代码路径
graph.add_edge("planner", "coder")
graph.add_edge("coder", "executor")

# 聊天路径
graph.add_edge("chatter", "supervisor")

# 搜索路径
graph.add_edge("researcher", "supervisor")

# 沙盒代码执行异常反馈环
graph.add_conditional_edges(
    "executor",
    lambda state: state["next_node"],
    {
        "coder": "coder",
        "END": "supervisor",
    },
)

graph = graph.compile(checkpointer=checkpoint)