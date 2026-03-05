from langgraph.graph import StateGraph, START, END
from agents.state_messages import StateMessages
from agents.planner import planner_node
from agents.engineer import engineer_node
from temp.executor import executor_node
from agents.chatter import chat_node
from agents.supervisor import supervisor_node
from agents.researcher import researcher_node
from agents.reporter import reporter_node
from langgraph.checkpoint.memory import InMemorySaver

checkpoint = InMemorySaver()

graph = StateGraph(StateMessages)
graph.add_node("chatter", chat_node)
graph.add_node("supervisor", supervisor_node)
graph.add_node("researcher", researcher_node)
graph.add_node("reporter", reporter_node)
graph.add_node("engineer", engineer_node)


graph.add_edge(START, "supervisor")

# 任务调度器
graph.add_conditional_edges(
    "supervisor",
    lambda state: state["next_node"],
    {
        "researcher": "researcher",
        "chatter": "chatter",
        "reporter": "reporter",
        "engineer": "engineer",
        "END": END, 
    },
)

# 聊天路径
graph.add_edge("chatter", "supervisor")

# 搜索路径
graph.add_edge("researcher", "supervisor")

# 报告总结路径
graph.add_edge("reporter", "supervisor")    

# 编码路径
graph.add_edge("engineer", "supervisor")

graph = graph.compile(checkpointer=checkpoint)