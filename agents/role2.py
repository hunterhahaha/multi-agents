"""
职责：接收角色一的处理结果并生成相对应的可执行的python代码，以纯字符串的形式只输出代码内容。
"""

from agents.llm import reasoner_model
from agents.role_prompts import role_2_prompts
from agents.state_messages import StateMessages
from langchain.messages import SystemMessage, HumanMessage
from langgraph.config import get_stream_writer  
from agents.writer_messages import Message
from time import time

def role_2_node(state: StateMessages):
    response = ""
    start_time = time()
    writer = get_stream_writer()  
    thinking = False
    
    for chunk in reasoner_model.stream(
        input=[SystemMessage(content=role_2_prompts)] + state.messages
    ):
        msg = chunk.additional_kwargs.get("reasoning_content")
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
                writer(Message(type="assistant", content="编码中...\n"))
            response += chunk.content
            writer(Message(type="assistant", content=chunk.content))
    writer(Message(type="assistant", content=f"\n编码完成，耗时{time() - start_time:.2f}秒\n"))
    return {"messages": [HumanMessage(content=response)], "code": response}    