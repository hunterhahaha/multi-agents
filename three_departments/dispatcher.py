from Cores.Models.model import chat_model
from Cores.States.structs import DispatcherStruct, GraphState
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import Literal
from Cores.Prompts.dispatcher import dispatcher_prompt
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

dispatcher = StateGraph(DispatcherStruct)

def dispatch(state: DispatcherStruct) -> DispatcherStruct:
    """
    进行意图判断，实现聊天和任务的分拣
    """
    class IntentJudge(BaseModel):
        intent_judge: Literal["chat", "task"]
        output: str = Field(description="结果为chat时，输出聊天内容；结果为task时，输出任务描述")
    
    messages = [
        SystemMessage(content=dispatcher_prompt),
        HumanMessage(content=state["user_input"])
    ]

    dispatch_llm = chat_model.with_structured_output(IntentJudge)

    result = dispatch_llm.invoke(messages)

    return {
        "intent_judge": result.intent_judge,
        "chat_reply": result.output if result.intent_judge == "chat" else None,
        "task": result.output if result.intent_judge == "task" else None,
    }

dispatcher.add_node(dispatch)

dispatcher.add_edge(START, "dispatch")
dispatcher.add_edge("dispatch", END)
dispatcher = dispatcher.compile()