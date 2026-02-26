from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv
import os

load_dotenv()

chat_model = ChatDeepSeek(
    model_name=os.environ.get("CHAT_MODEL"),
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    api_base=os.environ.get("DEEPSEEK_API_URL"),
    temperature=0,
)

reasoner_model = ChatDeepSeek(
    model_name=os.environ.get("REASONER_MODEL"),
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    api_base=os.environ.get("DEEPSEEK_API_URL"),
    temperature=0,
)