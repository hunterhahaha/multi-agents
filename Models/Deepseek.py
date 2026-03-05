"""Deepseek模型"""

from langchain.chat_models import init_chat_model
from .Base import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class DeepseekChatModel(BaseModel):
    """Deepseek聊天模型"""
    DEFAULT_API_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL_NAME = "deepseek-chat"
    def __init__(
            self, 
            api_key: Optional[str] = None, 
            api_url: Optional[str] = None, 
            model_name:Optional[str] = None, 
            temperature: float = 0
        ):
        """
        初始化Deepseek聊天模型

        Args:
        api_key: 模型API密钥
        api_url: 模型API地址
        model_name: 模型名称
        temperature: 模型温度
        """
        if api_key is None:
            try:
                api_key = os.environ.get("DEEPSEEK_API_KEY")
            except Exception:
                raise ValueError("DeepseekChatModel初始化失败，api_key不能为空")
            
        super().__init__(api_key, api_url, model_name, temperature)
        self.model = init_chat_model(
            model_name=model_name,
            api_key=api_key,
            api_base=api_url,
            temperature=temperature,
        )

    def _create_instance(self):
        return self.model
