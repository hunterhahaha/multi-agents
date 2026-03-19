from workers.researcher import researcher
from workers.analyst import analyst
from workers.writer import writer
from Cores.States.structs import ScehdulerState, TaskNode, DAG
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END



def dispatch(state: ScehdulerState):
    """
    分发器
    """
    ready = {}
    for task_id, task in state["reviewed_plan"].nodes.items():
        if task["status"] == "ready":
            ready[task["worker"]] = task
    
    if not ready:
        return END
    
    return [
        Send(
            worker,
            task
        )
        for worker, task in ready
    ]

def collect(state: ScehdulerState):
    """
    汇总器
    """
    # 更新正在运行的任务状态
    for task_id, task in state["reviewed_plan"].nodes.items():
        if task["status"] == "running" and task_id in state["finished"]:
            state["reviewed_plan"].nodes[task_id]["status"] = "done"
    
    # 处理失败任务
    if state["failed"]:
        for task_id in state["failed"]:
            if state.retry_count.get(task_id, 0) < 3:
                state["reviewed_plan"].nodes[task_id]["status"] = "pending"
                state.retry_count[task_id] = state.retry_count.get(task_id, 0) + 1
            else:
                raise Exception(f"任务 {task_id} 已经失败超过3次，停止重试")

    # 更新下一轮任务状态
    ready = []

    for task_id, task in state["reviewed_plan"].nodes.items():
        if task["status"] == "pending":
            dependencies = task["dependencies"]
            if all(state["reviewed_plan"].nodes[id]["status"] == "done" for id in dependencies):
                state["reviewed_plan"].nodes[task_id]["status"] = "ready"
                ready.append(task_id)
    
    return START