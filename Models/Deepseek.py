"""Deepseek模型"""

from langchain.chat_models import init_chat_model
from .Base import BaseModel

class DeepseekChatModel(BaseModel):
    """Deepseek聊天模型"""
    def __init__(self, api_key: str, api_url: str, model_name:str, temperature: float = 0):
        """
        初始化Deepseek聊天模型

        Args：
        api_key: 模型API密钥
        api_url: 模型API地址
        model_name: 模型名称
        temperature: 模型温度
        """
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