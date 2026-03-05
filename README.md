# Multi-Agents

基于 LangGraph 构建的多智能体系统。系统以「公司」为设计隐喻：**Supervisor 是最高管理者**，负责接收用户任务、制定调度决策；**各 Worker 是职能员工**，各司其职执行具体任务，并将结果汇报回 Supervisor。

---

## 系统架构

### 整体拓扑：星形调度

```
用户输入
   ↓
Supervisor（任务调度中枢）
   ├──→ Researcher（信息搜索）──→ Supervisor
   ├──→ Engineer（代码执行）───→ Supervisor
   ├──→ Reporter（结果整合）───→ Supervisor
   ├──→ Chatter（普通对话）───→ Supervisor
   └──→ END
```

所有 Worker 执行完成后必须回到 Supervisor，由 Supervisor 根据执行记录决定下一步。任何路径到达 END 之前，**必须经过 Reporter 进行结果整合**，这是架构层的强制约束，不依赖 LLM 的自由裁量。

### 调度流程

1. 用户输入进入 `Supervisor`
2. Supervisor 读取 `question` 和历史 `task_history`，决定调用哪个 Worker 及其任务内容
3. 指定 Worker 执行任务，将结果写入 `task_history` 后返回 Supervisor
4. Supervisor 根据执行结果决定继续调度或进入 Reporter → END

---

## State 设计

所有节点共享同一个 `StateMessages`，分为四层：

```python
class StateMessages(TypedDict):
    # 用户层
    question: str | None                               # 用户原始问题
    messages: Annotated[List[BaseMessage], add]        # 多轮对话历史

    # 调度层
    task: str | None                                   # Supervisor 派发给当前 Worker 的任务
    next_node: str | None                              # 下一个执行的节点名称

    # 执行层
    task_history: Annotated[List[TaskRecord], add]     # 所有已完成任务的执行记录

    # 输出层
    answer: str | None                                 # Reporter 写入的最终答案
```

`TaskRecord` 是每个 Worker 的标准化汇报格式：

```python
class TaskRecord(TypedDict):
    worker: str        # 执行者名称
    task: str          # 任务描述
    task_result: str   # 任务结果
    task_success: bool # 是否成功完成
```

---

## Worker 系统设计

### 设计原则

现有 Worker 之间存在大量重复代码——它们的执行骨架几乎完全相同，仅提示词和工具不同。为此，系统采用 **Template Method 模式 + Context Object 模式**，将不变的骨架封装在基类，将变化的部分通过钩子留给子类。

### 基础设施层

#### `LLMProvider` — 统一模型管理

```python
class LLMProvider:
    @classmethod
    def get(cls, model_type: Literal["chat", "reasoner", "vision"]) -> BaseChatModel:
        ...
```

所有 Worker 通过 `LLMProvider.get()` 获取模型，不直接依赖具体模型实例。切换模型、为不同 Worker 指定不同模型，只需修改此处。

#### `PromptTemplate` — 统一提示词管理

```python
class PromptTemplate:
    def render(self, **kwargs) -> str:
        return self.template.format(**kwargs)
```

每个 Worker 持有自己的 `PromptTemplate`，渲染逻辑统一由基类调用，消除各 Worker 对 prompt 格式化的不一致处理。

---

### `WorkerContext` — 执行上下文对象

所有 Worker 的执行状态统一用 Context 对象承载，避免将执行中间状态污染到全局 State。

```python
class WorkerContext:
    """基础上下文，所有 Worker 通用"""
    history: list          # 本次执行内的消息历史（循环内积累）
    task_success: bool
    task_result: str
```

有内部状态的 Worker（如 Engineer）通过继承扩展，**不需要新的基类分支**：

```python
class EngineerContext(WorkerContext):
    code: str = ""
    code_result: str = ""
    failure_count: int = 0
```

---

### `BaseWorker` — 执行骨架

循环逻辑、错误处理、TaskRecord 构建，**只写一次**：

```python
class BaseWorker:
    name: str                  # Worker 标识，对应 graph 节点名和 TaskRecord.worker
    description: str           # 供 Supervisor prompt 动态生成 node_choices
    prompt: PromptTemplate
    tools: list
    model_type: str = "chat"

    # 可覆盖的钩子（子类按需重写）
    def create_context(self, state) -> WorkerContext: ...
    def build_input(self, state, ctx) -> list: ...
    def on_tool_result(self, tool_name, args, result, ctx): ...
    def should_abort(self, ctx) -> bool: ...

    # 不可覆盖的执行骨架
    def run(self, state: StateMessages) -> dict: ...
```

#### 三个核心钩子覆盖所有已知差异化需求

| 钩子 | 用途 | 默认行为 |
|------|------|---------|
| `create_context` | 创建 Worker 专属上下文 | 返回基础 `WorkerContext` |
| `build_input` | 构建每轮 LLM 输入 | `[SystemMessage(prompt), *ctx.history]` |
| `on_tool_result` | 处理工具调用结果，更新 ctx | 追加消息到 `ctx.history` |
| `should_abort` | 定义提前退出条件 | 永远返回 `False` |

---

### Worker 子类示例

**简单 Worker（无需覆盖任何钩子）：**

```python
class ResearcherWorker(BaseWorker):
    name = "researcher"
    description = "需要搜索最新网络信息时使用"
    prompt = PromptTemplate(researcher_prompts)
    tools = [searxng_search, fetch_webpage, final_answer]
```

**复杂 Worker（覆盖需要定制的钩子）：**

```python
class EngineerWorker(BaseWorker):
    name = "engineer"
    description = "需要编写并执行 Python 代码时使用"
    prompt = PromptTemplate(engineer_prompts)
    tools = [python_code_box, final_answer]
    model_type = "reasoner"

    def create_context(self, state):
        return EngineerContext(state)

    def build_input(self, state, ctx: EngineerContext):
        return [
            SystemMessage(self.prompt.render(task=state["task"])),
            HumanMessage(f"用户原始问题：{state['question']}"),
            HumanMessage(f"代码状态：{ctx.model_dump_json()}"),
        ]

    def on_tool_result(self, tool_name, args, result, ctx: EngineerContext):
        if tool_name == "python_code_box":
            ctx.code = args["code"]
            ctx.code_result = result
            if result.startswith("Error:"):
                ctx.failure_count += 1

    def should_abort(self, ctx: EngineerContext):
        return ctx.failure_count >= 4
```

---

### `WorkerRegistry` — 中心化注册

Worker 的名称、描述、节点函数统一在 Registry 管理，消除在 `graph.py`、`supervisor.py`、`role_prompts.py` 三处写死的问题：

```python
class WorkerRegistry:
    @classmethod
    def register(cls, worker: BaseWorker): ...

    @classmethod
    def get_node_fn(cls, name: str):
        """返回 LangGraph 可用的节点函数"""

    @classmethod
    def get_supervisor_choices(cls) -> str:
        """动态生成 supervisor prompt 里的 node_choices 描述"""

    @classmethod
    def get_all_nodes(cls) -> list[tuple[str, Callable]]:
        """供 graph.py 批量注册节点"""
```

`graph.py` 变为纯配置，新增 Worker 零改动：

```python
# 注册所有 Worker
WorkerRegistry.register(ResearcherWorker())
WorkerRegistry.register(EngineerWorker())
WorkerRegistry.register(ReporterWorker())
WorkerRegistry.register(ChatterWorker())

# 批量加入 graph
for name, fn in WorkerRegistry.get_all_nodes():
    graph.add_node(name, fn)
    graph.add_edge(name, "supervisor")
```

---

## 变化点隔离总结

| 想改什么 | 改哪里 | 影响范围 |
|---------|--------|---------|
| 执行骨架、错误处理、日志 | `BaseWorker.run` | 所有 Worker 自动生效 |
| 某个 Worker 的特殊逻辑 | 对应 `XxxContext` + 钩子方法 | 只影响该 Worker |
| 新增 Worker | 新建一个类，Registry 注册 | 零改动旧代码 |
| 切换或新增模型 | `LLMProvider` | 一处生效 |
| 全局能力（限流、追踪等） | `BaseWorker.run` | 全局生效 |
| Supervisor 可调度的节点列表 | `WorkerRegistry` | 自动同步到 graph 和 prompt |

---

## 目录结构

```
multi-agents/
├── agents/
│   ├── base_worker.py        # BaseWorker 基类 + WorkerContext
│   ├── worker_registry.py    # WorkerRegistry
│   ├── workers/
│   │   ├── researcher.py
│   │   ├── engineer.py
│   │   ├── reporter.py
│   │   └── chatter.py
│   ├── supervisor.py
│   ├── state_messages.py
│   └── role_prompts.py
├── llms/
│   └── llm_provider.py       # LLMProvider
├── tools/
│   └── web_tools.py
├── sandbox/
│   └── box_langchain.py
├── graph.py                  # 纯拓扑配置，不含业务逻辑
└── main.py
```

---

## 扩展路径

当前系统是**扁平公司结构**，Supervisor 直管所有 Worker，适合当前规模。当 Worker 数量显著增长时，可引入「部门」层级：

```
Supervisor
├── 信息部门 Lead → Researcher, WebScraper, ...
└── 工程部门 Lead → Engineer, DataAnalyst, ...
```

届时 `BaseWorker` 和 `WorkerRegistry` 的设计天然支持这种扩展，无需重构底层。
