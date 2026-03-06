# Multi-Agents

基于 LangGraph 构建的多智能体系统，以**公司分层执行**为设计隐喻：

- 任务从上层进入，逐层分析、审核、拆解
- 最终产出一份结构化的 `ExecutionPlan`
- 再由专职调度者按计划驱动 Worker 执行

> **重构说明**：`agents/` 下的现有代码处于过渡期，不代表最终设计，以本文档为准。

---

## 架构总览

```
用户输入
   ↓
┌─────────────────────────────────┐
│  Dispatcher（分拣层）             │  判断是闲聊还是任务；任务才往下走
└─────────────────────────────────┘
   ↓ 任务
┌─────────────────────────────────┐
│  Planner（规划层）                │  理解目标 → 拆解子任务 → 输出 ExecutionPlan
└─────────────────────────────────┘
   ↓ Plan 草稿
┌─────────────────────────────────┐
│  Reviewer（审核层）               │  检查 Plan 质量，不合格直接打回 Planner
└─────────────────────────────────┘
   ↓ 审核通过
┌─────────────────────────────────┐
│  Scheduler（调度层）              │  读 Plan → 找可执行步骤 → 派发 Worker
│                          ↑      │  Worker 回报 → 更新步骤状态 → 继续或结束
└─────────────────────────────────┘
   ↓ / ↑
┌─────────────────────────────────┐
│  Workers（执行层）                │  Researcher / Engineer / Analyst / ...
│  各司其职，结果写入 task_history   │  每个 Worker 完成后回到 Scheduler
└─────────────────────────────────┘
   ↓ 全部步骤完成
Reporter → END
```

**两个关键设计原则：**
1. **计划与执行分离**：Planner 的产出是显式的 `ExecutionPlan`，Scheduler 只读 Plan 行动，不自行判断
2. **强制审核关卡**：Reviewer 是架构层的硬约束，Plan 未通过审核则打回重做，不依赖 LLM 自由裁量

---

## 各层职责

| 角色 | 类型 | 输入 | 输出 |
|------|------|------|------|
| **Dispatcher** | 路由节点 | `question` | `next_node`：`planner` 或 `END`（闲聊直接回） |
| **Planner** | LLM 节点 | `question` + `review_feedback`（重规划时） | `execution_plan` |
| **Reviewer** | LLM 节点 | `execution_plan` | `review_result`（approved / feedback） |
| **Scheduler** | 路由节点 | `execution_plan` + `task_history` | `next_node`（Worker 名）+ `task` |
| **Worker** | LLM 节点 | `task` | `task_history` 追加一条 `TaskRecord` |
| **Reporter** | LLM 节点 | `task_history` + `question` | `answer` |

---

## State 设计

```python
# ── 核心数据结构 ────────────────────────────────────────────

class TaskRecord(TypedDict):
    worker: str
    task: str
    task_result: str
    task_success: bool

class ExecutionStep(TypedDict):
    step_id: str              # 唯一 ID，如 "step_1"
    description: str          # 任务描述（传给 Worker 的 task 字段）
    assigned_worker: str      # Worker 名，必须在 WorkerRegistry 中注册
    dependencies: List[str]   # 前置步骤 step_id 列表，为空表示可立即执行
    status: str               # pending | running | done | failed

class ExecutionPlan(TypedDict):
    objective: str            # 本次任务目标，一句话概括
    steps: List[ExecutionStep]

class ReviewResult(TypedDict):
    approved: bool
    feedback: str             # 不通过时的具体意见，传回 Planner 重规划
    retry_count: int          # 防止无限循环，>= 2 时强制放行

# ── 全局 State ──────────────────────────────────────────────

class StateMessages(TypedDict):
    # 用户层
    question: str | None
    messages: Annotated[List[BaseMessage], add]

    # 规划层
    execution_plan: ExecutionPlan | None

    # 审核层
    review_result: ReviewResult | None

    # 调度层
    task: str | None
    next_node: str | None

    # 执行层
    task_history: Annotated[List[TaskRecord], add]

    # 输出层
    answer: str | None
```

---

## Graph 拓扑

Graph 分为两个阶段，拓扑语义不同：

```
# 分析阶段（有向无环）
dispatcher → planner → reviewer
                ↑           │ 封驳
                └───────────┘
                            │ 准奏
                            ↓
# 执行阶段（循环）
                        scheduler ──→ worker_A ──┐
                            ↑                    │
                            └────────────────────┘
                            │ 所有步骤完成
                            ↓
                        reporter → END
```

`graph.py` 只做拓扑配置，不含业务逻辑：

```python
# 分析阶段
graph.add_node("dispatcher", dispatcher_node)
graph.add_node("planner", planner_node)
graph.add_node("reviewer", reviewer_node)
graph.add_edge(START, "dispatcher")
graph.add_conditional_edges("dispatcher", dispatcher_router)   # → planner | END
graph.add_edge("planner", "reviewer")
graph.add_conditional_edges("reviewer", reviewer_router)       # → planner | scheduler

# 执行阶段
graph.add_node("scheduler", scheduler_node)
graph.add_node("reporter", reporter_node)
graph.add_conditional_edges("scheduler", scheduler_router)     # → worker_X | reporter

for name, fn in WorkerRegistry.get_all_nodes():
    graph.add_node(name, fn)
    graph.add_edge(name, "scheduler")                          # 所有 Worker 回 Scheduler

graph.add_edge("reporter", END)
```

---

## Worker 系统

Worker 设计沿用**模板方法模式**，骨架不变，差异通过钩子实现。

```
BaseWorker
├── name / description / prompt / tools / model_config（子类声明）
├── create_context()   → WorkerContext（可覆盖）
├── build_input()      → List[Message]（可覆盖）
├── on_tool_result()   → 工具结果处理（可覆盖）
└── run()              → 不可覆盖，执行骨架
```

新增 Worker 只需声明四个字段 + Registry 注册，零改动旧代码：

```python
class MyWorker(BaseWorker):
    name = "my_worker"
    description = "描述这个 Worker 的用途，供 Planner 感知"
    prompt = my_prompt
    tools = [some_tool]
    model_config = chat_model

WorkerRegistry.register(MyWorker())
```

> **未来扩展**：`WorkerRegistry` 设计支持运行时动态注册，为后续「自由创建 Worker」功能预留接口。

---

## 模型层

模型类是**参数容器 + 工厂**，只负责持有配置和返回实例，调用逻辑由 Worker 负责。

```python
# 使用方式：模块级单例，全局复用
from Models.Deepseek import chat_model, reasoner_model
```

新增厂商只需继承 `BaseModel`，覆盖 `DEFAULT_API_URL` / `DEFAULT_MODEL_NAME` / `_create_instance()`。

---

## 目录结构

```
multi-agents/
├── Models/
│   ├── base.py                  # BaseModel 基类
│   └── deepseek.py              # DeepseekChatModel + 模块级单例
│
├── agents/
│   ├── state.py                 # 所有 TypedDict：TaskRecord / ExecutionStep / ExecutionPlan / ReviewResult / StateMessages
│   ├── base_worker.py           # BaseWorker + WorkerContext
│   ├── worker_registry.py       # WorkerRegistry
│   │
│   ├── pipeline/                # 分析-审核管线（非 Worker 角色）
│   │   ├── dispatcher.py        # 分拣：闲聊 vs 任务
│   │   ├── planner.py           # 规划：生成 ExecutionPlan
│   │   ├── reviewer.py          # 审核：准奏 / 封驳
│   │   └── scheduler.py         # 调度：读 Plan 派发 Worker
│   │
│   └── workers/                 # 执行层 Worker
│       ├── researcher.py
│       ├── engineer.py
│       ├── reporter.py
│       └── chatter.py
│
├── tools/
│   └── web_tools.py
│
├── sandbox/
│   └── box_langchain.py
│
├── graph.py                     # 纯拓扑配置
└── main.py
```

---

## 变化点隔离

| 想改什么 | 改哪里 | 影响范围 |
|---------|--------|---------|
| 执行骨架、错误处理 | `BaseWorker.run` | 所有 Worker 自动生效 |
| 某个 Worker 的特殊逻辑 | 对应钩子方法 | 只影响该 Worker |
| **新增 Worker** | 新建类 + Registry 注册 | 零改动旧代码 |
| Reviewer 审核标准 | `reviewer.py` 的 prompt | 只影响审核层 |
| Planner 规划策略 | `planner.py` 的 prompt | 只影响规划层 |
| 切换模型 | `Models/` 对应配置 | 一处生效 |
| Graph 拓扑 | `graph.py` | 只影响流向 |

---

## 扩展路径

**当前阶段**：单 Planner 生成完整 Plan，Scheduler 串行/依赖调度。

**下一阶段**（Worker 数量增多时）：Planner 可拆分为 Director + 多个 DeptPlanner 并行分析，汇总后再统一出 Plan。

**未来**：`WorkerRegistry` 支持运行时动态注册，实现「按需创建 Worker」。
