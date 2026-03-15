from graph import graph
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from langchain_core.runnables import RunnableConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
executor = ThreadPoolExecutor()
config: RunnableConfig = {"configurable": {"thread_id": "1"}}

@app.get("/debug/ping")
async def ping():
    return {"status": "ok", "message": "服务运行中"}

@app.post("/chat")
async def chat(body: dict):
    user_input = body["message"]
    logger.info(f"收到请求：{user_input}")
    def sync_generator():
        """封装同步生成器，stream会同步阻塞"""
        for stream_mode, chunk in graph.stream(
            input={"question": user_input, "messages": [("user", user_input)], "answer": ""},
            stream_mode=["custom", "updates"],
            config=config
        ):
            if stream_mode == "custom":
                yield chunk["content"]

    async def async_generator():
        """把同步生成器包装成异步生成器"""
        loop = asyncio.get_event_loop()
        gen = sync_generator()
        while True:
            chunk = await loop.run_in_executor(executor, lambda: next(gen, None))
            if chunk is None:
                break
            yield chunk

    return StreamingResponse(
        async_generator(),
        media_type="text/plain; charset=utf-8"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)



"""
while(True):
        user_input = input("我:")
        if user_input == "exit":
            break
        for stream_mode, chunk in graph.stream(
            input={"question": user_input, "messages": [("user", user_input)]},
            stream_mode=["custom", "updates"]
        ):
            if stream_mode == "custom":
                print(chunk["content"], end="", flush=True)
"""