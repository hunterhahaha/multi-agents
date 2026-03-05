from pydantic import BaseModel, Field
from typing import Literal
from llms.llm import chat_model
from agents.state_messages import StateMessages
from agents.role_prompts import supervisor_prompts
from langgraph.config import get_stream_writer
from langchain.messages import SystemMessage, HumanMessage
from agents.writer_messages import Message

class Supervisor_decision(BaseModel):
    task: str = Field(description="下一个节点需要完成的任务，如果是END，任务为空")
    next_node: Literal[
        "researcher",
        "chatter",
        "reporter",
        "engineer",
        "END",
    ] = Field(description="下一步执行的节点")

supervisor = chat_model.with_structured_output(Supervisor_decision)

def supervisor_node(state: StateMessages):
    writer = get_stream_writer()

    writer(Message(type="supervisor", content="调度中...\n"))

    task_config = ""

    # 拼接任务日志
    if state.get("task_history"):
        for task_record in state["task_history"]:
            task_config += f"""
                任务执行者：{task_record["worker"]}
                任务描述：{task_record["task"]}
                任务结果：{task_record["task_result"]}
                任务状态：{task_record["task_success"]}
                """

    decision = supervisor.invoke(
        input=[
            SystemMessage(content=supervisor_prompts.format(
                    task_record=task_config
                )
            ),
            HumanMessage(content=f"问题：{state["question"]}"),
        ]
    )

    if decision.next_node != "END":
        writer(Message(type="supervisor", content=f"下一步节点：{decision.next_node}\n"))
        writer(Message(type="supervisor", content=f"任务：{decision.task}\n"))

        return {
            "task": decision.task,
            "next_node": decision.next_node,
        }

    elif decision.next_node == "END":
        return {
            "task": decision.task,
            "next_node": decision.next_node,
        }