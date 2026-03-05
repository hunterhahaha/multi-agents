"""
职责：处理用户的问题，将用户的问题清晰化和流程化，传递给后续的角色进行代码生成。
"""

from llms.llm import reasoner_model, chat_model
from agents.role_prompts import planner_prompts
from langchain.messages import SystemMessage, HumanMessage
from agents.state_messages import StateMessages
from langgraph.config import get_stream_writer
from agents.writer_messages import Message
from time import time

def planner_node(state: StateMessages):
    response = ""
    start_time = time()
    writer = get_stream_writer()  

    if state["use_reasoner"]:
        thinking = False
        for chunk in reasoner_model.stream(
            input=[SystemMessage(content=planner_prompts)] + state["messages"]
        ):
            msg = chunk.additional_kwargs.get('reasoning_content')
            if msg:
                if not thinking:
                    thinking = True
                    start_time = time()
                    writer(Message(type="thinking", content="思考中...\n"))
                writer(Message(type="thinking", content=msg))
            else:
                if thinking:
                    thinking = False
                    writer(Message(type="thinking", content=f"\n思考完成，耗时{time() - start_time:.2f}秒\n"))
                    start_time = time()
                    writer(Message(type="assistant", content="分析问题...\n"))
                response += chunk.content
                writer(Message(type="assistant", content=chunk.content))
        writer(Message(type="assistant", content=f"\n分析完成，耗时{time() - start_time:.2f}秒\n"))
    else:
        start_time = time()
        writer(Message(type="assistant", content="问题分析...\n"))
        for chunk in chat_model.stream(
            input=[('system', planner_prompts)] + state["messages"] 
        ):
            response += chunk.content
            writer(Message(type="assistant", content=chunk.content))
        writer(Message(type="assistant", content=f"\n分析完成，耗时{time() - start_time:.2f}秒\n"))

    return {"messages": [HumanMessage(content=response)]}