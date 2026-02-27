"""
职责：处理用户的问题，将用户的问题清晰化和流程化，传递给后续的角色进行代码生成。
"""

from langchain.agents import create_agent
from agents.llm import reasoner_model
from langgraph.checkpoint.memory import InMemorySaver
from agents.role_prompts import role_1_prompts

checkpointer = InMemorySaver()

role_1 = create_agent(
    model=reasoner_model,
    system_prompt=role_1_prompts,
    checkpointer=checkpointer,
)

from agents.state_messages import StateMessages

def role_1_node(state: StateMessages):
    messages = state.messages

    thinking = False

    for mode, chunk in role_1.stream(
        {"messages": messages},
        stream_mode=["messages", "updates"],
    ):
        # 显式思考过程
        if mode == "messages":
            message, metadata = chunk
            if message.additional_kwargs:
                if not thinking:
                    thinking = True
                    print("思考中...")
                print(message.additional_kwargs.get("reasoning_content"), end="", flush=True)
        # 更新状态
        if mode == "updates":
            return {
                "messages": [chunk['model']["messages"][-1]],
                "answer": chunk['model']["messages"][-1].content,
            }
