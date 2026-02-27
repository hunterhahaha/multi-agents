"""
职责：接收用户问题和运行角色二的代码获取结果，结合结果优化并回答用户问题。
"""

from langchain.agents import create_agent
from agents.llm import chat_model
from agents.role_prompts import role_3_prompts
from langchain.messages import SystemMessage, AIMessage
from sandbox.box_langchain import code_box

tools = [code_box]

role_3 = create_agent(
    model=chat_model,
    system_prompt=role_3_prompts,
    tools=tools
)

from agents.state_messages import StateMessages

def role_3_node(state: StateMessages):
    response = ""
    
    print("最终回答...")
    for mode, chunk in role_3.stream(
        input={"messages": state.messages},
        stream_mode=["messages"]
    ):
        message, metadata = chunk
        response += message.content
        print(message.content, end="", flush=True)
    print("\n回答完成...")
    return {"messages": [AIMessage(content=response)], "answer": response}