from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    model=os.environ.get("MODEL_NAME"),
    api_key=os.environ.get("MODEL_API_KEY"),
    base_url=os.environ.get("MODEL_URL"),
    temperature=0,
)
