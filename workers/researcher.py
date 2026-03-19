"""
researcher.py - 研究员角色，负责信息检索、笔记整理和报告撰写。
"""

from tools.web_tools import (
    searxng_search,
    fetch_webpage,
    save_note,
)
from Cores.Agents.Base import BaseAegnt
from Cores.Models.model import chat_model
from langgraph.graph import StateGraph, START, END

researcher = StateGraph()