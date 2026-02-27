"""
职责：处理用户的问题，将用户的问题清晰化和流程化，传递给后续的角色进行代码生成。
"""

from agents.llm import reasoner_model, chat_model
from agents.role_prompts import role_1_prompts

from agents.state_messages import StateMessages

def role_1_node(state: StateMessages):
    response = ""

    if state.use_reasoner:
        thinking = False
        for chunk in reasoner_model.stream(
            input=[('system', role_1_prompts), state.question]
        ):
            if chunk.additional_kwargs:
                if not thinking:
                    thinking = True
                    print("思考中...")
                print(chunk.additional_kwargs['reasoning_content'], end="", flush=True)
            else:
                if thinking:
                    thinking = False
                    print("\n思考完成...")
                response += chunk.content
    else: 
        