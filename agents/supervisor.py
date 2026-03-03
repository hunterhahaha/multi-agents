from pydantic import BaseModel, Field
from typing import Literal
from agents.llm import chat_model
from agents.state_messages import StateMessages
from agents.role_prompts import supervisor_prompts
from langgraph.config import get_stream_writer
from langchain.messages import SystemMessage, HumanMessage
from agents.writer_messages import Message
from time import time

class Supervisor_decision(BaseModel):
    next_node: Literal[
        "planner",
        "researcher",
        "chatter",
        "END"
    ] = Field(description="下一步执行的节点")
    use_reasoner: bool = Field(description="是否使用推理模型")
    decision_reason: str = Field(description="决策原因，一句话概括。")

supervisor = chat_model.with_structured_output(Supervisor_decision)

def supervisor_node(state: StateMessages):
    writer = get_stream_writer()

    writer(Message(type="thinking", content="决策中...\n"))
    start_time = time()

    decision = supervisor.invoke(
        input=[
            SystemMessage(content=supervisor_prompts.format(
                have_answer=bool(state.get("answer")),
                answer=state.get("answer", ""),
            )),
            HumanMessage(content=f"问题：{state["question"]}"),
        ]
    )

    writer(Message(type="thinking", content=f"决策完成，耗时{time() - start_time:.2f}秒\n"))
    writer(Message(type="thinking", content=f"下一步节点：{decision.next_node}\n"))
    writer(Message(type="thinking", content=f"决策原因：{decision.decision_reason}\n"))

    return {
        "next_node": decision.next_node,
        "use_reasoner": decision.use_reasoner,
    }