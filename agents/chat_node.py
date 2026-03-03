from agents.llm import chat_model, reasoner_model
from agents.state_messages import StateMessages
from langgraph.config import get_stream_writer  
from agents.writer_messages import Message
from time import time

def chat_node(state: StateMessages):
    """
    聊天节点
    """
    prompt = """
    你是一个聊天助手，负责回答用户的问题。
    """
    start_time = time()
    writer = get_stream_writer()  
    response = ""
    
    if state["use_reasoner"]:
        thinking = False
        for chunk in reasoner_model.stream(
            input=[("system", prompt)] + state["messages"]
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
                    writer(Message(type="assistant", content="聊天助手： "))
                writer(Message(type="assistant", content=chunk.content))
                response += chunk.content
    
    else:
        writer(Message(type="assistant", content="聊天助手： "))
        for chunk in chat_model.stream(
            input=[("system", prompt)] + state["messages"]
        ):
            response += chunk.content
            writer(Message(type="assistant", content=chunk.content))

    writer(Message(type="assistant", content=f"\n聊天完成...耗时{time() - start_time:.2f}秒\n"))
    
    return {"messages": [("assistant", response)], "answer": response}