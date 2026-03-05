"""Deepseek模型"""

from langchain.chat_models import init_chat_model
from .Base import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class DeepseekChatModel(BaseModel):
    """Deepseek聊天模型"""
    def __init__(
            self, 
            api_key: Optional[str] = None, 
            api_url: Optional[str] = None, 
            model_name:Optional[str] = None, 
            temperature: float = 0
        ):
        """
        初始化Deepseek聊天模型

        Args：
        api_key: 模型API密钥
        api_url: 模型API地址
        model_name: 模型名称
        temperature: 模型温度
        """
        # 参数为空从本地获取
        if api_key is None:
            try:
                api_key = os.environ["DEEPSEEK_API_KEY"]
            except Exception as e:
                print("未提供API密钥且环境变量中未找到DEEPSEEK_API_KEY")
                return e
        if api_url is None:
            try:
                api_url = os.environ["DEEPSEEK_API_URL"]
            except Exception as e:
                print("未提供API URL且环境变量中未找到DEEPSEEK_API_URL")
                return e
        if model_name is None:
            try:
                model_name = os.environ["DEEPSEEK_MODEL_NAME"]
            except Exception as e:
                print("未提供模型名称且环境变量中未找到DEEPSEEK_MODEL_NAME")
                return e

        super().__init__(api_key, api_url, model_name, temperature)
        self.model = init_chat_model(
            model_name=model_name,
            api_key=api_key,
            api_base=api_url,
            temperature=temperature,
        )

    def invoke(self, system_prompt: str, user_prompt: str):
        """
        调用模型接口

        Args：
        system_prompt：系统提示词
        user_prompt： 用户输入

        Returns：
        模型生成的回复
        """
        try:
            messages = [
                ("system", system_prompt),
                ("user", user_prompt),
            ]

            return self.model.invoke(messages)
        except Exception as e:
            print(f"调用Deepseek模型出错：{e}")
            return e