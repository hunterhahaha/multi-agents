"""
writer返回的数据格式
"""

from typing import TypedDict

# 基类
class Message(TypedDict):
    type: str
    content: str