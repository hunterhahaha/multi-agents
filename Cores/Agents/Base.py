from langchain_core.tools import tool
from langchain.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import Optional

class BaseAegnt:
    def __init__(
            self,
            model: BaseChatModel | None = None,
            tools: Optional[list[tool]] = [],
    ):
        if model is None:
            raise ValueError("模型不能为空")

        self.model = model
        self.tools = tools
        self.functions_map: dict[str, tool] = {} # 工具映射表，tool_name -> tool

        if self.tools:
            self.bind_with_tools(self.tools)

    def invoke(self, input: list[BaseMessage]):
        """
        智能体调用
        能够自循环运行工具
        若配置了强制结构工具，统一命名为 final_answer，工具调用结束后会返回 final_answer 的结果
        """
        try:
            input_copy = input.copy()

            while True:
                response = self.model.invoke(input_copy)
                input_copy.append(AIMessage(content=response.content))
                if response.response_metadata["finish_reason"] == "stop":
                    return response
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_result = ""

                    if tool_name == "structured_output_tool":
                        return self.functions_map[tool_name].invoke(tool_args)
                    else:
                        tool_result = self.functions_map[tool_name].invoke(tool_args)
                        input_copy.append(HumanMessage(content=f"工具 {tool_name} 的结果: {tool_result}"))

        except Exception as e:
            return f"agent invoke error: {e}"

    def bind_with_tools(self, tools: list[tool] = []):
        """
        绑定工具，并创建工具映射
        
        Args:
        tools: 工具列表

        可以对 agent 的 tools 进行追加
        """
        if tools:
            self.tools.extend(tools)
        self.functions_map = {tool.name: tool for tool in self.tools}
        self.model = self.model.bind_tools(self.tools)