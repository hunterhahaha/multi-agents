# multi-agents 项目规划

## 项目概述
基于 LangGraph 构建的多智能体代码执行助手。用户输入自然语言问题，系统自动判断是否需要编程解决，
若需要则经过需求分析 → 代码生成 → 沙盒执行 → 结果回答的完整链路，并具备代码执行失败的自动重试反馈环。

## 当前架构（已完成）

### 节点结构
- **supervisor**（`Supervisor_agent.py`）：任务调度核心，基于结构化输出决策下一步节点
- **planner / role1**（`role1.py`）：需求分析专家，将用户问题拆解为结构化任务规格
- **coder / role2**（`role2.py`）：代码生成器，使用推理模型生成可执行 Python 代码
- **executor / role3**（`role3.py`）：代码执行器，调用沙盒工具执行代码并优化回答
- **chatter / chat_node**（`chat_node.py`）：普通对话处理节点

### 执行流程
START → supervisor
supervisor → planner（代码任务）/ chatter（普通对话）/ END（任务完成）
planner → coder → executor
executor → supervisor（正常完成，汇报结果）
executor → coder（代码报错，触发反馈环，最多重试3次）
chatter → supervisor（完成后汇报）


### 关键特性
- Supervisor 循环决策：每次子 Agent 完成后汇报，Supervisor 判断是否结束
- 代码执行反馈环：executor 捕获 ToolMessage 中的 Error，立即 break stream，打回 coder 重写
- 流式输出：全链路 custom stream，支持 thinking / assistant 两种消息类型
- 对话记忆：InMemorySaver checkpoint，同一 thread_id 保持上下文

### 文件结构
multi-agents/
├── main.py # FastAPI 服务，/chat 接口，流式响应
├── graph.py # LangGraph 图定义，节点注册和边连接
├── agents/
│ ├── Supervisor_agent.py # Supervisor 节点
│ ├── role1.py # Planner 节点
│ ├── role2.py # Coder 节点
│ ├── role3.py # Executor 节点
│ ├── chat_node.py # Chatter 节点
│ ├── state_messages.py # 全局 State 定义（TypedDict）
│ ├── role_prompts.py # 所有角色 Prompt 模板
│ ├── llm.py # LLM 实例（chat_model / reasoner_model）
│ └── writer_messages.py # 流式消息类型定义
└── sandbox/
└── box_langchain.py # Python 代码沙盒工具（subprocess）


---

## 下一阶段规划

### 阶段一：重命名与代码清理（短期）
- [ ] role1 → planner，role2 → coder，role3 → executor
- [ ] 删除已弃用的 `intent_node.py`
- [ ] 修复 graph.py 中 `END` 对象作为字典 key 的 bug，改为字符串 `"END"`
- [ ] State 中补充 `code_result` 字段，executor 将执行结果单独存储而不混入 messages

### 阶段二：扩展 Agent 能力（中期）
目标：让各 Agent 具备真正的工具调用能力，而不仅是 LLM 调用链

- [ ] **Researcher Agent**：新增搜索 Agent，集成 Tavily/Serper 等搜索工具
  - Supervisor 可以在需要外部信息时调度 Researcher
  - 搜索结果作为上下文传递给 Planner 或直接回答用户
- [ ] **Planner 工具化**：为 planner 添加任务分解工具，支持将复杂任务拆成多个子任务
- [ ] **沙盒安全加固**：当前 sandbox 使用 subprocess 直接执行，考虑引入 Docker 隔离或 RestrictedPython

### 阶段三：真正的多智能体协同（长期）
目标：Agent 之间可以互相调用，而不是只能通过 Supervisor 中转

- [ ] **Agent 间直接通信**：使用 LangGraph 的 Subgraph 功能，每个 Agent 拥有独立的内部图
- [ ] **并行执行**：Planner 拆解出多个独立子任务时，使用 `Send()` API 并行分发给多个 Coder 实例
- [ ] **Reviewer Agent**：新增代码审查 Agent，coder 生成代码后先经 reviewer 检查再执行，减少低级错误
- [ ] **动态 Agent 注册**：Supervisor 可以根据任务类型动态选择调用哪些 Agent，而不是固定节点集合

### 阶段四：工程化（配套）
- [ ] **持久化存储**：将 InMemorySaver 替换为 SqliteSaver 或 PostgresSaver，支持服务重启后历史恢复
- [ ] **多会话管理**：thread_id 改为动态生成，支持多用户并发
- [ ] **前端页面**：构建对话管理界面，支持查看 thinking 过程、多会话切换
- [ ] **监控日志**：记录每次 Agent 调用耗时、token 消耗、重试次数等指标

---

## 设计原则
1. **最小改动优先**：新增能力通过加节点实现，不破坏已有链路
2. **流式优先**：所有节点保持 custom stream 输出，保证用户体验
3. **LLM vs Agent 实例按需选择**：只有需要自主选择工具的节点才用 create_agent，其余保持 LLM 实例减少开销
4. **Supervisor 是唯一的全局决策者**：子 Agent 只负责执行，不做全局路由判断
