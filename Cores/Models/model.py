from .Deepseek import DeepseekChatModel 
from dotenv import load_dotenv
import httpx 
import os

load_dotenv()

http_client = httpx.Client(
    limits=httpx.Limits(
        max_keepalive_connections=5,
        keepalive_expiry=30,
    )
)

chat_model_config = DeepseekChatModel(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    api_url=os.environ.get("DEEPSEEK_API_URL"),
    model_name=os.environ.get("DEEPSEEK_CHAT_MODEL"),
    temperature=0,
    http_client=http_client
)

reasoner_model_config = DeepseekChatModel(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    api_url=os.environ.get("DEEPSEEK_API_URL"),
    model_name=os.environ.get("DEEPSEEK_REASONER_MODEL"),
    temperature=0,
    http_client=http_client
)

chat_model = chat_model_config.build()
reasoner_model = reasoner_model_config.build()

# test
if __name__ == "__main__":
    from pydantic import BaseModel
    from langchain.tools import tool
    class Text(BaseModel):
        text: str

    class FinalAnswer(BaseModel):
        final_answer: Text

    @tool
    def create_final_answer(final_answer: FinalAnswer) -> FinalAnswer:
        """生成最终答案"""
        return final_answer

    llm_witg_tool = chat_model.bind_tools([create_final_answer],tool_choice="create_final_answer")

    response = llm_witg_tool.invoke(
        input=("你好")
    )
    
    if response.tool_calls:
        tool_calls = response.tool_calls
        tool_name = tool_calls[0]["name"]
        tool_args = tool_calls[0]["args"]

        if tool_name == "create_final_answer":
            response = create_final_answer.invoke(tool_args)
        
    print(response.final_answer.text)
    