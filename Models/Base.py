"""基础模型类"""

from abc import ABC, abstractmethod

class BaseModel(ABC):
    """模型基类"""
    def __init__(self, api_key: str, api_url: str, model_name:str, temperature: float = 0):
        """
        初始化模型

        Args：
        api_key: 模型API密钥
        api_url: 模型API地址
        model_name: 模型名称
        temperature: 模型温度
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model_name = model_name
        self.temperature = temperature

    @abstractmethod
    def invoke(self, system_prompt: str, user_prompt: str):
        """
        调用模型接口

        Args：
        system_prompt: 系统提示语
        user_prompt: 用户输入

        Returns：
        模型输出结果
        """
        pass