from tools.web_tools import (
    searxng_search,
    fetch_webpage,
    save_note,
)
from Cores.Agents.Base import BaseAegnt
from Cores.Models.model import chat_model
from langgraph.graph import StateGraph, START, END

analyst = StateGraph()