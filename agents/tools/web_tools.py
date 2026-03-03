import os

os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

import requests
from langchain.tools import tool
from langchain_community.document_loaders import WebBaseLoader

SEARXNG_URL = "http://localhost:8080/search"

@tool
def searxng_search(query: str) -> str:
    """
    使用Searxng搜索引擎搜索关键词，返回标题、URL和摘要。
    适合用于查找最新信息、新闻、文档等。
    """
    try:
        response = requests.get(
            SEARXNG_URL,
            params={
                "q": query,
                "format": "json",
                "language": "zh-CN",
            },
            timeout=10,
        )
        data = response.json()
        results = data.get("results", [])[:5]
        if not results:
            return "未找到相关结果"
        output = []
        for i, r in enumerate(results, 1):
            output.append(
                f"{i}. [{r.get("title", "无标题")}]\n"
                f"URL: {r.get("url", "")}\n"
                f"摘要: {r.get("content", "无摘要")[:200]}"
            )
        return "\n\n".join(output)
    except Exception as e:
        return f"搜索过程中出错: {str(e)}"
    
@tool
def fetch_webpage(url: str) -> str:
    """
    根据URL抓取网页的完整内容，用于深度阅读页面详情。
    在searxng_search拿到URL后，用此工具获取页面全文。
    """
    try:
        loader = WebBaseLoader(url)
        loader.requests_kwargs = {"timeout": 10}
        docs = loader.load()
        content = docs[0].page_content[:4000] if docs else "无法获取内容"
        return content
    except Exception as e:
        return f"加载页面内容时出错: {str(e)}"