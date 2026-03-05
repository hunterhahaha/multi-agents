from agents.role_prompts import reporter_prompts
from llms.llm import chat_model
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from agents.state_messages import StateMessages, TaskRecord
from langgraph.config import get_stream_writer
from agents.writer_messages import Message

def reporter_node(state: StateMessages):
    """
    报告整合节点，负责将团队所有成员的工作成果整合为一份完整、清晰的最终答案呈现给用户。
    """
    task_result = ""
    task_success = False
    task_config = ""

    writer = get_stream_writer()

    writer(Message(type="reporter", content="总结中...\n"))

    try:
        # 拼接任务日志
        for task_record in state["task_history"]:
            task_config += f"""
                任务执行者：{task_record["worker"]}
                任务描述：{task_record["task"]}
                任务结果：{task_record["task_result"]}
                任务状态：{task_record["task_success"]}
                """
            
        input = [
            SystemMessage(content=reporter_prompts),
            HumanMessage(content=f"""
            用户问题：{state["question"]}
            任务记录：{task_config}
            """),
        ]

        for chunk in chat_model.stream(input):
            writer(Message(type="reporter", content=chunk.content))
            task_result += chunk.content

        writer(Message(type="reporter", content="\n"))
        task_success = True

        return {
            "messages": [AIMessage(content=task_result)],
            "answer": task_result,

            "task_history": [
                TaskRecord(
                    worker="reporter",
                    task=task_record["task"],
                    task_result=task_result,
                    task_success=task_success,
                )
            ],
        }
    except Exception as e:
        writer(Message(type="reporter", content=f"总结失败：{e}\n"))
        
        return {
            "task_history": [
                TaskRecord(
                    worker="reporter",
                    task=task_record["task"],
                    task_result=task_result,
                    task_success=task_success,
                )
            ],
        }