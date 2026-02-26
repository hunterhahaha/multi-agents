"""
agents.role1 的 Docstring
职责：处理用户的问题，将用户的问题清晰化和流程化，传递给后续的角色进行代码生成。
"""

from langchain.agents import create_agent
from agents.llm import reasoner_model
from langgraph.checkpoint.memory import InMemorySaver
from agents.role_prompts import role1_prompts

checkpointer = InMemorySaver()

role_1 = create_agent(
    model=reasoner_model,
    system_prompt=role1_prompts,
    checkpointer=checkpointer,
)

# 正则化提取模型决策
import re

def parse_next_node(content: str) -> tuple:
    match = re.search(r'<next_node>\s*(role_2|END)\s*</next_node>', content, re.IGNORECASE)
    clean_content = re.sub(r'<next_node>.*?</next_node>', '', content, flags=re.IGNORECASE | re.DOTALL).strip()
    if match:
        next_node = match.group(1).strip()
        return next_node, clean_content
    
    return "END", clean_content

from agents.state_messages import StateMessages

def role_1_node(state: StateMessages):
    messages = state.messages

    thinking = False

    for mode, chunk in role_1.stream(
        {"messages": messages},
        stream_mode=["messages", "updates"],
    ):
        if mode == "messages":
            message, metadata = chunk
            if message.additional_kwargs:
                if not thinking:
                    thinking = True
                    print("思考中...")
                print(message.additional_kwargs.get("reasoning_content"), end="", flush=True)
        if mode == "updates":
            next_node, clean_content = parse_next_node(chunk['model']['messages'][-1].content)
            return {
                "messages": messages + [("assistant", clean_content)], 
                "next_node": next_node, 
                "answer": clean_content if next_node == "END" else "",
            }
