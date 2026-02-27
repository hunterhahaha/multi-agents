from agents.llm import chat_model, reasoner_model
from agents.state_messages import StateMessages

def chat_node(state: StateMessages):
    """
    聊天节点
    """
    prompt = """
    你是一个聊天助手，负责回答用户的问题。
    """
    response = ""
    if state.use_reasoner:
        thinking = False
        chat = False
        for chunk in reasoner_model.stream(
            input=[("system", prompt), ('user', state.question)]
        ):
            if chunk.additional_kwargs:
                if not thinking:
                    thinking = True
                    print("思考中...")
                print(chunk.additional_kwargs['reasoning_content'], end="", flush=True)
            else:
                if thinking:
                    thinking = False
                    print("\n思考完成，开始对话...")
                response += chunk.content
                print(chunk.content, end="", flush=True)
        if not chat:
            chat = True
            print("\n对话完成...")
    else:
        chat = False
        print("开始对话...")
        for chunk in chat_model.stream(
            input=[("system", prompt), ('user', state.question)]
        ):
            response += chunk.content
            print(chunk.content, end="", flush=True)
        if not chat:
            chat = True
            print("\n对话完成...")
    return {"messages": [("assistant", response)], "answer": response}