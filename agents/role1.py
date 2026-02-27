"""
职责：处理用户的问题，将用户的问题清晰化和流程化，传递给后续的角色进行代码生成。
"""

from agents.llm import reasoner_model, chat_model
from agents.role_prompts import role_1_prompts
from langchain.messages import SystemMessage, AIMessage
from agents.state_messages import StateMessages

def role_1_node(state: StateMessages):
    response = ""

    if state.use_reasoner:
        thinking = False
        for chunk in reasoner_model.stream(
            input=[SystemMessage(content=role_1_prompts)] + state.messages
        ):
            msg = chunk.additional_kwargs.get('reasoning_content')
            if msg:
                if not thinking:
                    thinking = True
                    print("思考中...")
                print(msg, end="", flush=True)
            else:
                if thinking:
                    thinking = False
                    print("\n思考完成，分析问题...")
                response += chunk.content
                print(chunk.content, end="", flush=True)
        print("分析完成...")
    else:
        print("问题分析...")
        for chunk in chat_model.stream(
            input=[('system', role_1_prompts)] + state.messages 
        ):
            response += chunk.content
            print(chunk.content, end="", flush=True)
        print("分析完成...")
    
    return {"messages": [AIMessage(content=response)]}