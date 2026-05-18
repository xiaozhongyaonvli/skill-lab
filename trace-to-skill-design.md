# trace-to-skill-design

## 状态

设计草案，已与当前 `trace-to-skill/` 第一版实现对齐。

## 当前理解

目标是做一个“从用户操作中反向提炼 skill”的 skill。

当前共识：

- 正式触发别名采用：
  - `@trace-start`
  - `@trace-stop`
- 记录过程需要结构化，而不是简单保存原始对话
- 这个 skill 的职责收敛为：
  - 提取 SOP
  - 生成 skill 草稿
  - 不承担后续的评审、上下文工程优化、记忆体系设计

## 职责边界

`trace-to-skill` 的定位是：

- workflow capture
- SOP synthesis
- draft skill generation

它负责把一次真实协作过程沉淀成“可复用流程草稿”，而不是直接产出一个已经充分优化完成的成熟 skill。

### 负责内容

- 显式开始记录与显式结束记录
- 结构化记录事件流
- 从事件流中提炼稳定的 SOP
- 归纳触发条件、输入、步骤、决策点、输出
- 输出 skill 草稿
- 提出可抽取脚本、引用资料、资产的建议

### 不负责内容

- 对生成出的 skill 做完整质量评审
- 对上下文工程做深入优化
- 设计或优化 multi-agent 架构
- 审计 subagent 间上下文重叠
- 处理 truth surface 冲突或多份真相源治理
- 设计记忆分层或长期记忆策略
- 设计 KV cache / prompt prefix 等高级提示工程策略
- 把草稿自动打磨成最终成熟 skill

### 分层建议

当前先只做第一层：

1. `trace-to-skill`
   - 负责 `trace -> structured events -> SOP -> draft skill`

后续如果继续扩展，再单独做：

2. skill 评审层
   - 评估 skill 质量
   - 评估 context engineering 结构
   - 识别 truth surface、subagent overlap、上下文冗余等问题

3. skill 优化层
   - 根据评审结果改写 skill
   - 优化 context、references、scripts、prompt 排布等

这样做的原因是：

- 触发边界清晰
- 输出预期稳定
- 每个 skill 的能力职责单一
- 避免 `trace-to-skill` 变成过于臃肿的总控 skill

## 用户使用方式

从用户视角，这个 skill 应该只有两个显式动作：

1. `@trace-start`
2. `@trace-stop`

中间阶段目标是 0 侵入：

- 用户正常工作
- 用户不需要手动写事件
- 用户不需要维护 capture 路径
- 用户不需要分类步骤
- 用户不需要接触 JSONL 或内部状态文件

也就是说，结构化记录属于 skill 的内部职责，不属于用户职责。

这条边界要保持严格：

- 用户只看见开始和结束
- 用户不接触中间记录机制
- 用户不接触 capture 状态管理
- 用户不接触内部脚本分层

## 运行时目标

为了贴近 `@trace-start` / `@trace-stop` 的体验，skill 内部运行时应满足：

- 维护单一 active capture 状态
- 开始时自动注册 active capture
- 结束时通过单一收口动作完成 stop + synthesize
- 用户不需要手动传 capture 目录

## 用户入口

如果需要脚本入口，也只保留两类用户入口：

- `trace_start.py`
- `trace_stop.py`

其余脚本全部视为内部实现，不作为用户流程的一部分。

预期流程：

1. 当用户显式调用 `@trace-start` 时，开始记录。
2. 在记录窗口内，持续把用户的操作写入某个文件。
3. 当用户显式调用 `@trace-stop` 时，结束记录。
4. 从这段时间内的操作记录中提取可复用 SOP。
5. 将提取结果整理成一个新的 skill 草稿，至少包含：
   - skill 名称建议
   - 触发描述
   - 核心工作流
   - 可抽取的脚本、引用资料、资产建议
   - `SKILL.md` 初稿

## 我建议的 skill 边界

这个 skill 先只负责“记录 + 提炼 SOP + 输出 skill 草稿”，不直接做：

- 自动安装到 `~/.codex/skills`
- 自动发布
- 自动覆盖已有 skill
- 在没有显式开始/结束标记时隐式记录整段对话
- 直接完成上下文工程评审
- 直接完成 skill 优化与重构

这样边界更稳，第一版更容易验证。

## 建议的产物

根目录下建议有两类文件：

- 运行期记录文件
  - 例如：`captures/<session-id>.md` 或 `captures/<session-id>.jsonl`
- 提炼后的 skill 草稿
  - 例如：`draft-skills/<skill-name>/SKILL.md`
  - 或先输出单文件草稿：`draft-skills/<skill-name>.md`

## 建议的输入输出

### 开始记录

输入示例：

```text
@trace-start
```

预期行为：

- 创建或打开当前记录文件
- 写入开始时间、会话标识、触发命令
- 后续持续追加操作事件

### 结束记录

输入示例：

```text
@trace-stop
```

预期行为：

- 关闭当前记录窗口
- 汇总本次窗口中的操作
- 生成 skill 草稿

## 关键设计点

### 1. “操作”具体指什么

可能有三种口径：

- 只记录用户消息
- 记录用户消息 + assistant 的关键动作
- 记录用户消息 + assistant 动作 + 生成的文件/命令摘要

当前结论：

- 不只记录用户消息
- 采用结构化事件记录
- 默认记录：
  - 用户输入
  - assistant 关键动作
  - 文件改动
  - 结果摘要
- 选记：
  - 命令摘要
- 不记录：
  - 完整内部推理
  - 全量终端输出
  - 低价值碎步骤
  - 全量逐字对话

原因：

- 只记用户输入，无法还原可复用 pipeline
- 全量原始记录噪声太大，不利于后续提炼 skill
- 结构化事件最适合后续归纳成“触发条件 / 输入 / 步骤 / 决策 / 输出”

### 1.1 建议的事件模型

建议把记录对象统一成事件流，事件类型先控制在少量高价值类别：

- `user_request`
- `assistant_action`
- `file_change`
- `decision`
- `result`

每条事件至少包含：

- `timestamp`
- `type`
- `summary`
- `artifacts`
- `tags`

可选字段：

- `command`
- `files`
- `reason`
- `outcome`
- `next_step`

示意：

```json
{
  "timestamp": "2026-04-03T10:30:00+08:00",
  "type": "assistant_action",
  "summary": "读取 README 和现有 skill 目录结构，确认仓库组织方式",
  "files": ["README.md", "interest-to-pr-finder/SKILL.md"],
  "tags": ["discovery", "context"]
}
```

### 2. 记录格式

候选方案：

- Markdown
  - 好读，便于人工整理
  - 结构化分析较弱
- JSONL
  - 便于后处理、提取步骤、做过滤
  - 人工直接阅读稍弱

当前结论：

- 主记录格式用 `JSONL`
- 汇总展示用 `Markdown`

这样既便于机器提炼，也便于人工复查。

### 3. 提炼结果的粒度

候选方案：

- 只生成需求摘要
- 生成 `SKILL.md` 草稿
- 生成完整 skill 目录骨架

当前结论：

- 第一版先稳定生成 `SKILL.md` 草稿
- 是否自动初始化完整 skill 目录，作为第二阶段能力

这样可以先把“提炼质量”做好，再决定是否自动化脚手架。

## 第一版最小闭环

第一版建议只做这几个能力：

1. 响应开始记录命令
2. 将记录窗口内的结构化事件落盘
3. 响应结束记录命令
4. 生成一个 skill 草稿 markdown
5. 在草稿中明确区分：
   - 原始操作
   - 归纳后的流程
   - 可以复用的资源建议

## 建议的提炼输出结构

结束记录后，建议固定产出这些段落：

1. 本次记录摘要
2. 触发这个 pipeline 的典型用户意图
3. 输入上下文与依赖材料
4. 结构化 SOP
5. 关键决策点与判断规则
6. 输出产物
7. 可抽取脚本建议
8. `SKILL.md` 草稿

这样后续转正式 skill 时，信息不会散。

## 待确认问题

1. 结束后你要的是：
   - 单个 markdown 草稿
   - 完整 skill 目录
   - 两者都要

## 正式命名建议

如果你还没定正式名，我建议从下面几个里选：

- `operation-to-skill`
- `skill-capture`
- `workflow-recorder`
- `trace-to-skill`

我当前最推荐：`trace-to-skill`

## 建议的第一版目录

如果继续往下做，我建议最终目录先长这样：

```text
trace-to-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── start_capture.py
│   ├── append_event.py
│   ├── stop_capture.py
│   └── synthesize_skill.py
├── references/
│   └── event-schema.md
└── assets/
    └── capture-template.json
```

其中：

- `start_capture.py` 负责初始化记录窗口
- `append_event.py` 负责追加结构化事件
- `stop_capture.py` 负责关闭记录窗口
- `synthesize_skill.py` 负责把事件流整理成 skill 草稿
