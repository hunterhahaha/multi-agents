"""
职责：接收角色一的处理结果并生成相对应的可执行的python代码，以纯字符串的形式只输出代码内容。
"""

from agents.llm import reasoner_model
from agents.role_prompts import role_2_prompts
from agents.state_messages import StateMessages
from langchain.messages import SystemMessage, HumanMessage

def role_2_node(state: StateMessages):
    response = ""

    thinking = False
    for chunk in reasoner_model.stream(
        input=[SystemMessage(content=role_2_prompts)] + state.messages
    ):
        msg = chunk.additional_kwargs.get("reasoning_content")
        if msg:
            if not thinking:
                print("思考中...")
                thinking = True
            print(msg, end="", flush=True)
        else:
            if thinking:
                thinking = False
                print("\n思考完毕，编码中...")
            response += chunk.content
            print(chunk.content, end="", flush=True)
    print("\n编码完毕...")
    return {"messages": [HumanMessage(content=response)], "code": response}    