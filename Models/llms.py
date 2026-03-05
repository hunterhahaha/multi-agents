from langchain_deepseek import ChatDeepSeek
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

chat_model = ChatDeepSeek(
    model_name=os.environ.get("CHAT_MODEL"),
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    api_base=os.environ.get("DEEPSEEK_API_URL"),
    temperature=0,
    http_client=http_client,
)

reasoner_model = ChatDeepSeek(
    model_name=os.environ.get("REASONER_MODEL"),
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    api_base=os.environ.get("DEEPSEEK_API_URL"),
    temperature=0,
    http_client=http_client,
)