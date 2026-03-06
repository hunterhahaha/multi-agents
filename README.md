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

## 模型层设计

### 设计原则

模型类是**参数容器 + 工厂**，职责只有一个：持有构建 LangChain 模型实例所需的所有参数，并通过 `build()` 返回可用的实例。**调用逻辑不属于模型层**，由 Worker 层负责。

### `BaseModel` — 模型配置基类

```python
class BaseModel(ABC):
    DEFAULT_API_URL: str = ""       # 子类覆盖，提供厂商默认地址
    DEFAULT_MODEL_NAME: str = ""    # 子类覆盖，提供默认模型名称

    def __init__(self, api_key, api_url=None, model_name=None, temperature=0):
        # api_key 为空直接抛异常，不 return e
        # api_url / model_name 为 None 时自动使用子类的 DEFAULT_*
        ...

    @abstractmethod
    def _create_instance(self) -> BaseChatModel:
        """子类实现：返回具体的 LangChain 模型实例"""
        pass

    def build(self) -> BaseChatModel:
        """第一次调用时创建实例并缓存，之后复用同一个实例"""
        if self._instance is None:
            self._instance = self._create_instance()
        return self._instance

    def rebuild(self) -> BaseChatModel:
        """强制重建实例，用于参数变更后刷新"""
        self._instance = None
        return self.build()
```

`build()` 的核心价值：同一份配置在多个 Worker 中共享时，只创建一次实例，所有人复用；`rebuild()` 统一刷新，不需要逐处重建。

### 厂商子类示例：`DeepseekChatModel`

```python
class DeepseekChatModel(BaseModel):
    DEFAULT_API_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL_NAME = "deepseek-chat"

    def __init__(self, api_key=None, api_url=None, model_name=None, temperature=0):
        # api_key 优先用传入值，否则从环境变量读取
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        super().__init__(api_key, api_url, model_name, temperature)

        # 使用 self.* 而非原始参数，确保 DEFAULT_* 默认值已生效
        self.model = init_chat_model(
            model_name=self.model_name,
            api_key=self.api_key,
            api_base=self.api_url,
            temperature=self.temperature,
        )

    def _create_instance(self):
        return self.model
```

### 模块级单例

实际使用时在 `Models/` 底部直接创建实例，所有文件 import 同一个对象（Python 模块天然单例）：

```python
# Models/Deepseek.py 底部
chat_model = DeepseekChatModel()
reasoner_model = DeepseekChatModel(model_name="deepseek-reasoner", temperature=1.0)
```

```python
# 任意 Worker 文件
from Models.Deepseek import chat_model, reasoner_model
```

---

## Worker 系统设计

### 设计原则

所有 Worker 的执行骨架完全相同，差异只在提示词和工具。采用 **Template Method 模式**：骨架写在基类，变化点通过钩子留给子类。

**终止条件和业务约束（如最大重试次数）交给提示词和工具管理**，不放在基类骨架里，保持基类的纯粹性。

### 工具调用机制

Worker 通过 LangChain 的 `bind_tools` 让 LLM 感知工具列表。LLM 需要调用工具时返回 `tool_calls`，不需要时返回 `content` 作为最终结果。每次 `invoke` 对 LLM 来说是独立的，通过 `ctx.history` 把上一轮工具结果传入，实现多轮工具调用的连贯性。

工具 dispatch 使用**名称查找表**（方案 A），新增工具无需修改任何 `if/elif`：

```python
tool_map = {tool.name: tool for tool in self.tools}
result = tool_map[tool_call["name"]].invoke(tool_call["args"])
```

### `WorkerContext` — 执行上下文

Worker 执行期间的临时状态不污染全局 State，统一用 Context 对象承载：

```python
class WorkerContext:
    def __init__(self):
        self.history: list = []      # 本轮循环内积累的消息（工具结果追加在此）
        self.task_result: str = ""
        self.task_success: bool = False
```

有额外内部状态的 Worker 通过继承扩展，不需要新的基类分支：

```python
class EngineerContext(WorkerContext):
    def __init__(self):
        super().__init__()
        self.code: str = ""
        self.code_result: str = ""
```

### `BaseWorker` — 执行骨架

```python
class BaseWorker(ABC):

    # ── 子类必须声明 ──────────────────────────────
    name: str            # Worker 标识，对应 graph 节点名和 TaskRecord.worker
    description: str     # 供 WorkerRegistry 动态生成 supervisor prompt 用
    prompt: str          # 提示词
    tools: list = []     # 工具列表，无工具的 Worker 保持空列表
    model_config = ...   # 指向 Models/ 里的某个模型实例

    # ── 可覆盖的钩子（子类按需重写）──────────────
    def create_context(self, state) -> WorkerContext:
        return WorkerContext()

    def build_input(self, state, ctx) -> list:
        return [SystemMessage(self.prompt), *ctx.history, HumanMessage(state["task"])]

    def on_tool_result(self, tool_call, result, ctx):
        ctx.history.append(ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"]
        ))

    # ── 不可覆盖的执行骨架 ────────────────────────
    def run(self, state) -> dict:
        ctx = self.create_context(state)
        tool_map = {tool.name: tool for tool in self.tools}

        model = self.model_config.build()
        if self.tools:
            model = model.bind_tools(self.tools)

        try:
            while True:
                response = model.invoke(self.build_input(state, ctx))

                # 无 tool_calls：LLM 认为任务完成，直接用 content 作为结果
                if not response.tool_calls:
                    ctx.task_result = response.content or ""
                    ctx.task_success = bool(response.content)
                    break

                tool_call = response.tool_calls[0]
                result = tool_map[tool_call["name"]].invoke(tool_call["args"])
                self.on_tool_result(tool_call, result, ctx)

        except Exception as e:
            ctx.task_result = str(e)
            ctx.task_success = False

        return {"task_history": [TaskRecord(
            worker=self.name,
            task=state["task"],
            task_result=ctx.task_result,
            task_success=ctx.task_success,
        )]}
```

### 各 Worker 覆盖哪些钩子

| Worker | `create_context` | `build_input` | `on_tool_result` |
|--------|:-:|:-:|:-:|
| ChatterWorker | ✗ | ✗ | ✗ |
| ResearcherWorker | ✗ | ✗ | ✗ |
| ReporterWorker | ✗ | ✅ 需要拼入 task_history | ✗ |
| EngineerWorker | ✅ 返回 EngineerContext | ✅ 带代码状态 | ✅ 更新 code 字段 |

### Worker 子类示例

**最简 Worker（只需声明，无需覆盖）：**

```python
class ResearcherWorker(BaseWorker):
    name = "researcher"
    description = "需要搜索最新网络信息时使用"
    prompt = researcher_prompts
    tools = [searxng_search, fetch_webpage]
    model_config = chat_model
```

**复杂 Worker（覆盖差异化钩子）：**

```python
class EngineerWorker(BaseWorker):
    name = "engineer"
    description = "需要编写并执行 Python 代码时使用"
    prompt = engineer_prompts
    tools = [python_code_box]
    model_config = reasoner_model

    def create_context(self, state):
        return EngineerContext()

    def build_input(self, state, ctx: EngineerContext):
        return [
            SystemMessage(self.prompt),
            HumanMessage(f"任务：{state['task']}"),
            HumanMessage(f"上一轮代码：{ctx.code}"),
            HumanMessage(f"上一轮结果：{ctx.code_result}"),
        ]

    def on_tool_result(self, tool_call, result, ctx: EngineerContext):
        super().on_tool_result(tool_call, result, ctx)
        ctx.code = tool_call["args"].get("code", "")
        ctx.code_result = result
```

---

## WorkerRegistry — 中心化注册

Worker 的名称、描述、节点函数统一在 Registry 管理，消除在 `graph.py`、`supervisor.py`、`role_prompts.py` 三处写死的问题：

```python
class WorkerRegistry:
    @classmethod
    def register(cls, worker: BaseWorker): ...

    @classmethod
    def get_supervisor_choices(cls) -> str:
        """动态生成 supervisor prompt 里的 node_choices 描述"""

    @classmethod
    def get_all_nodes(cls) -> list[tuple[str, Callable]]:
        """供 graph.py 批量注册节点"""
```

`graph.py` 变为纯拓扑配置，新增 Worker 零改动旧代码：

```python
WorkerRegistry.register(ResearcherWorker())
WorkerRegistry.register(EngineerWorker())
WorkerRegistry.register(ReporterWorker())
WorkerRegistry.register(ChatterWorker())

for name, fn in WorkerRegistry.get_all_nodes():
    graph.add_node(name, fn)
    graph.add_edge(name, "supervisor")
```

---

## 变化点隔离总结

| 想改什么 | 改哪里 | 影响范围 |
|---------|--------|---------|
| 执行骨架、错误处理 | `BaseWorker.run` | 所有 Worker 自动生效 |
| 某个 Worker 的特殊逻辑 | 对应 `XxxContext` + 钩子方法 | 只影响该 Worker |
| 新增 Worker | 新建一个类，Registry 注册 | 零改动旧代码 |
| 切换或新增模型 | `Models/` 对应配置类 | 一处生效 |
| Supervisor 可调度的节点列表 | `WorkerRegistry` | 自动同步到 graph 和 prompt |

---

## 目录结构

```
multi-agents/
├── Models/
│   ├── Base.py               # BaseModel 基类
│   ├── Deepseek.py           # DeepseekChatModel + 模块级实例
│   └── llms.py               # 过渡期兼容，后续由 Models/ 统一替代
├── agents/
│   ├── base_worker.py        # BaseWorker + WorkerContext
│   ├── worker_registry.py    # WorkerRegistry
│   ├── workers/
│   │   ├── researcher.py
│   │   ├── engineer.py
│   │   ├── reporter.py
│   │   └── chatter.py
│   ├── supervisor.py
│   ├── state_messages.py
│   └── role_prompts.py
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

`BaseWorker` 和 `WorkerRegistry` 的设计天然支持这种扩展，无需重构底层。
