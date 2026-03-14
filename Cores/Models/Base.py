from abc import ABC, abstractmethod
from langchain.chat_models import BaseChatModel
from typing import Optional

class BaseModel(ABC):
    DEFAULT_API_URL: str = ""
    DEFAULT_MODEL_NAME: str = ""
    def __init__(
        self,
        api_key: str,
        api_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0,
    ):
        if not api_key:
            raise ValueError(f"{self.__class__.__name__}初始化失败，api_key不能为空")

        self.api_key = api_key
        self.api_url = api_url or self.DEFAULT_API_URL
        self.model_name = model_name or self.DEFAULT_MODEL_NAME
        self.temperature = temperature

        self._instance: BaseChatModel | None = None

    @abstractmethod
    def _create_instance(self):
        """
        返回模型实例。
        只在第一次调用 build() 时执行。
        
        关于子类的使用，直接返回子类的实例。
        
        ps：预接口，目前不打算使用
        """
        pass

    def build(self) -> BaseChatModel:
        """
        返回模型实例。
        第一次调用时创建，之后复用同一个实例。
        
        ps：预接口，目前不打算使用
        """
        if self._instance is None:
            self._instance = self._create_instance()
        return self._instance
    
    def rebuild(self) -> BaseChatModel:
        """
        强制重建实例。
        用于参数改变后的刷新。

        ps：预接口，目前不打算使用
        """
        self._instance = None
        return self.build()
    
    def __repr__(self) -> str:
        """返回模型相关信息"""
        return (
            f"{self.__class__.__name__}"
            f"(api_url={self.api_url}, "
            f"model_name={self.model_name}," 
            f"temperature={self.temperature})"
        )