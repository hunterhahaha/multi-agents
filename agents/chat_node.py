from agents.llm import chat_model, reasoner_model
from agents.state_messages import StateMessages
from langgraph.config import get_stream_writer  

def chat_node(state: StateMessages):
    """
    聊天节点
    """
    prompt = """
    你是一个聊天助手，负责回答用户的问题。
    """
    writer = get_stream_writer()  
    response = ""
    if state.use_reasoner:
        thinking = False
        for chunk in reasoner_model.stream(
            input=[("system", prompt), ('user', state.question)]
        ):
            msg = chunk.additional_kwargs.get('reasoning_content')
            if msg:
                if not thinking:
                    thinking = True
                    writer("思考中...\n")
                writer(msg)
            else:
                if thinking:
                    thinking = False
                    writer("思考完成...\n")
                    writer("聊天助手： ")
                writer(chunk.content)
                response += chunk.content
    else:
        writer("聊天助手： ")
        for chunk in chat_model.stream(
            input=[("system", prompt), ('user', state.question)]
        ):
            response += chunk.content
            writer(chunk.content)
    return {"messages": [("assistant", response)], "answer": response}