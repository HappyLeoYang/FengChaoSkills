# FengChaoSkills 产品设计与开发总体规划

> 版本：v1.0（蓝图版）
> 日期：2026-07-07
> 性质：本文档是 FengChaoSkills 从 demo 走向成熟开源项目的总设计文档。任何后续开发者应先读本文档，再读 `CLAUDE.md` 和 `skills/fengchao-business-memory/` 下的规则文件。
> 读者：项目维护者、后续参与开发的工程师、（部分章节）未来的开源贡献者。

---

## 第一部分：项目理解 —— FengChaoSkills 是什么

### 1.1 要解决的问题

AI 编程会话是无状态的。一个长期项目中最昂贵的知识不是代码——代码在 git 里——而是**业务语义**：

- 为什么审核要分两级？
- "主管"这个词在这个团队里指什么岗位？
- 用户上个月明确否定过哪个方案？
- 哪个字段的实际含义和字面意思不一样？
- 哪里有踩过的坑，改动时必须绕开？

这些知识只存在于对话中。交付完成、会话关闭，知识就死了。下一个会话里用户被迫重新解释业务，AI 还可能犯一个更危险的错误：**把"讨论过但没做"当成"已经实现"，把"用户随口一提"当成"业务规则"，把"已废弃的旧行为"当成"当前行为"。**

FengChaoSkills 解决的就是这两个问题：**业务记忆的丢失**和**业务记忆的污染**。

### 1.2 一句话定义

> FengChaoSkills 是一个 Agent 无关的、基于 Markdown + Git 的**项目业务事实账本**：它让 AI 会话在真实开发交付后自动沉淀"业务真相 + 落地证据"，在新会话开始时按最小必要集合路由回这些记忆，并严格区分"当前事实"与"历史参考"。

### 1.3 它不是什么（与三类主流工具的本质区别）

| 物种 | 代表 | 回答的问题 | 时间方向 | FengChao 与它的区别 |
|------|------|-----------|----------|---------------------|
| Spec 驱动开发 | OpenSpec、GitHub Spec Kit | "AI 接下来应该做什么" | 事前（先规范后编码） | 它们的 truth 是需求规范；FengChao 的 truth 是业务认知（为什么、术语、边界、坑、否定项）。**可共存**：OpenSpec 管变更生命周期，FengChao 管业务认知生命周期 |
| 文件型项目记忆 | Cline Memory Bank、CLAUDE.md 约定 | "AI 上次做到哪了" | 进行中（同步工程状态） | 它们记工程进度和架构，无可信度分层，更新靠自觉；FengChao 记业务语义，有认识论分层和触发门禁 |
| 向量/平台记忆层 | mem0/OpenMemory、Zep、ByteRover | "用户是谁、说过什么" | 全程自动抽取 | 它们是黑盒数据库，面向个性化；FengChao 是 git 内可审查、可 review、可回滚的 Markdown，面向团队共享的业务事实 |

FengChao 有两个市面上**基本没人做**的设计，是本项目的差异化护城河：

1. **记忆的认识论分层**：五级可信度 + 冲突优先级（`business-context` > `task-records/changelog` > implemented plan > `conversation-records` > proposed plan）。所有主流工具都把"记住的东西"当同一等级的事实，而 AI 协作中最危险的错误恰恰是层级混淆。
2. **否定记忆**：`conversation-records` 中的 `--rejected`（用户明确否定过的方案）。AI 最招人烦的行为之一就是把用户拒绝过的方案再提一遍；Spec 工具不记这个，Memory Bank 没这个字段，mem0 的合并去重甚至可能把它当冗余消掉。

### 1.4 四个核心设计原则（本项目的灵魂，不可破坏）

1. **记忆有可信度等级**。六个目录不是文件分类，是认识论分层：当前真相 / 落地证据 / 历史参考，冲突时有明确优先级。
2. **写入有触发边界**。只有真实开发交付才能写证据层（`trigger_policy: after-real-development-only`）；讨论、Plan、只读分析不许污染记忆。
3. **真相有证据链**。每条业务认知必须能追溯到任务记录；`check` 强制校验链接完整性。不是"我记得是这样"，而是"这条规则由某任务落地，证据在这"。
4. **读取有路由**。FengWang 保证新会话加载"最小必要上下文"（8–12 个文件），而不是全量历史。

### 1.5 六层记忆模型

| 目录 | 语义 | 可变性 | 写入时机 |
|------|------|--------|----------|
| `business-context/` | 当前业务真相 | 可变（始终代表最新） | 仅当稳定业务事实已落地 |
| `task-records/` | 已交付任务的业务意图、最终方案、证据 | 不可变 | 仅真实开发交付后 |
| `changelog/` | 已落地变更历史 | 不可变 | 仅真实开发交付后 |
| `plan-records/` | 最终计划（proposed/approved/implemented/…） | 状态可更新 | Plan 产出最终计划后 |
| `conversation-records/` | 用户业务解释、术语、偏好、否定项 | 不可变 | 用户给出长期有价值的业务解释后 |
| `fengwang/` | 路由入口（FENGWANG.md + memory-map.md） | 持续追加 | 所有写入命令都追加路由行 |

隐私默认：只保存萃取摘要，永不保存完整对话。

### 1.6 现状盘点（截至 2026-07：demo 版）

**已有**（且质量不错）：
- 单文件零依赖 CLI（`fengchao.py`），init/fengwang/plan/conversation/maintain/check/inspect 七个子命令闭环。
- 六层记忆的目录、模板、索引、memory-map 追加逻辑。
- `check` 的链接完整性校验和 `--require-records-for-git-changes` 硬校验雏形。
- 端到端测试（subprocess 调真实 CLI，不 mock）。
- `references/` 下一套完整的模式规则文档（这是核心 prompt 资产）。

**缺失/粗糙**（本文档第二、三部分就是为了解决它们）：
- 侵入性过强：`init` 向目标项目复制 **5 份完整 skill 副本**、新建 6 个顶层记忆目录、直接创建 CLAUDE.md/opencode.json 整文件。
- 无停用/卸载/升级机制。
- 触发完全依赖 prompt 约定，agent 忘了执行就没有记忆——这是同类工具（Memory Bank）被诟病最多的失败模式。
- 路由是简单子串匹配打分，记录到几百条后会成为价值瓶颈。
- 模板内容三处并存（`fengchao.py` 内联 / `templates/` / `adapters/`），人工同步必然失配。
- 无版本概念、无发布渠道、无英文模板。

---

## 第二部分：产品设计 —— 走向成熟必须做的事

按四条主线组织。每项给出：为什么必要、设计要点、验收标准。

### 主线 A：低侵入 —— 轻易引入、无感使用、轻松停用

> 这是开源定位的第一优先级。调研结论（见第四部分）：OpenSpec 和 Spec Kit 都**没有文档化的卸载方式**。"引入无痛、停用无残留"是市面精品的集体盲区，要做成 FengChao 的招牌。

#### A1. 安装布局重构：单一安装点 + 单一记忆根

**为什么**：当前 `init` 在目标项目产生 5 份 skill 副本 + 6 个顶层目录 + 3 个整文件，对一个"轻量不打扰"的工具来说侵入太强，也让卸载几乎不可能干净。

**目标布局**：

```text
target-project/
├── .fengchao/                        # 唯一工具安装点（可整体删除）
│   ├── config.yaml
│   └── skill/                        # skill 的唯一完整副本
│       ├── SKILL.md
│       ├── references/
│       └── scripts/fengchao.py
├── fengchao/                         # 唯一记忆根（用户数据，属于用户，默认入 git）
│   ├── FENGWANG.md                   # 路由入口上移到记忆根，一眼可见
│   ├── memory-map.md
│   ├── business-context/
│   ├── task-records/
│   ├── changelog/
│   ├── plan-records/
│   └── conversation-records/
├── .claude/skills/fengchao-business-memory/SKILL.md    # 薄入口（按需，仅 frontmatter + 指向 .fengchao/skill/）
├── .cursor/rules/fengchao.mdc                          # 薄入口（按需）
└── CLAUDE.md / AGENTS.md 中的 marker 块（按需追加，见 A3）
```

**设计要点**：
- 新增配置键 `memory_root`（默认 `fengchao`），六个子目录键保留作为兼容项；老布局（六目录散在根下）继续可读，`status` 提示可迁移。
- 各 agent 目录只放**薄入口文件**（内容为 frontmatter + 一句"读取 `.fengchao/skill/SKILL.md` 并遵循"），不再复制整个 skill。不用软链接（Windows/git 兼容性差）。
- `init` 支持 `--agents claude,cursor,codex,opencode,agents`；不传时自动探测（存在 `.claude/`、`.cursor/` 等目录则勾选），探测不到则交互询问，非 TTY 环境默认全装薄入口。

**验收标准**：`init` 后目标项目新增顶层可见目录 ≤ 2 个（`.fengchao/` + 记忆根）；skill 正文在目标项目中只存在一份。

#### A2. 生命周期命令：`enable` / `disable` / `uninstall` / `status`

**为什么**：用户要求"想停用也能非常轻松地停用"。停用 ≠ 卸载 ≠ 删数据，三者必须分离。

**命令设计**：

| 命令 | 行为 | 不动什么 |
|------|------|----------|
| `fengchao disable` | 摘除 CLAUDE.md/AGENTS.md 中的 marker 块、删除各 agent 薄入口和 rule 文件、移除 hook 注册；在 config 写 `enabled: false` | 记忆数据、`.fengchao/` 本体全部保留 |
| `fengchao enable` | disable 的精确逆操作 | — |
| `fengchao uninstall` | disable + 删除 `.fengchao/`；打印记忆根位置并明确告知"记忆数据已保留" | **永不自动删除记忆根**；`--purge-memory` 需要交互式二次确认才删 |
| `fengchao status` | 显示：版本、启用状态、已接入的 agent、记忆根位置、各层记录数、最近一条记录日期、check 健康度 | 只读 |

**验收标准**：`disable` 后 `git diff` 干净可读（只有 marker 块消失）；`disable && enable` 后项目与之前逐字节一致；`uninstall` 默认绝不触碰记忆数据。

#### A3. 所有写入宿主文件的内容一律 marker 块化

**为什么**：当前 `AGENTS.md` 用 marker 追加（对），但 `CLAUDE.md` 是 `write_if_missing` 整文件（用户已有 CLAUDE.md 时静默跳过，行为不一致，且无法干净移除）；`opencode.json` 直接整文件创建。

**设计要点**：
- 统一规则：凡写入用户已有/可能已有的文件（CLAUDE.md、AGENTS.md），一律以 `<!-- FENGCHAO-BUSINESS-MEMORY:START/END -->` 包裹追加；文件不存在则创建后追加。
- `opencode.json` 若已存在则不覆盖，改为打印手工合并指引（JSON 无注释语法，无法安全 marker 化，宁可不动用户文件）。
- marker 块内容尽量短（≤ 15 行）：只写触发边界 + "读 `.fengchao/skill/SKILL.md`"，细则全部留在 skill 内部。宿主文件里的字越少，侵入感越低。

**验收标准**：对已有 CLAUDE.md/AGENTS.md/opencode.json 的项目执行 `init`，用户原内容一字不动；`disable` 能精确摘除全部注入。

### 主线 B：可靠性 —— 让记忆维护"必然发生"而不是"希望发生"

> 这是产品成败的最大风险点。结构设计再好，agent 不执行维护动作就一切归零。Memory Bank 的最大痛点（官方文档自己承认"依赖主动更新，疏忽则记录滞后"）必须在这里被正面解决。

#### B1. Hook 硬门禁（Claude Code 优先，其他 agent 渐进）

**为什么**：prompt 约定是软的，hook 是硬的。这是"用户不需要操心，它自行维护记忆"的唯一可靠实现路径。

**设计要点**（以 Claude Code hooks 为第一目标）：
- 新增子命令 `fengchao hook <event>`，由 `init --with-hooks`（默认开启，可 `--no-hooks`）向 `.claude/settings.json` 注册：
  - **SessionStart**：`fengchao hook session-start` 输出 additionalContext——"本项目启用 FengChao，先读 `fengchao/FENGWANG.md` 按需路由"。让路由自动发生，用户无需记得提醒 AI。
  - **Stop**：`fengchao hook stop-gate` 检查"存在项目 git 变更（排除记忆目录自身）但当天无 task/changelog 记录"。命中时按 `hook_mode` 行动：
    - `remind`（默认）：输出非阻塞提示，附上现成的 `maintain` 命令骨架；
    - `strict`：按 Claude Code hook 协议返回 block + reason，要求 agent 先完成记忆维护再结束回复；
    - `off`：跳过。
- **防打扰设计**（必须做，否则违背"不打扰"定位）：同一会话最多提醒一次（以 hook 收到的 session id 在 `.fengchao/tmp/` 落防重标记）；纯记忆目录变更不触发；无 git 仓库时静默跳过；hook 自身执行必须 < 500ms。
- 非 Claude Code 的 agent：提供可选的 git `pre-commit` 钩子（`fengchao install-git-hook`，默认不装），行为等同 `check --require-records-for-git-changes --warn`。

**验收标准**：在启用 hooks 的项目中，完成一次真实代码修改后直接结束会话，agent 会被提示（remind）或被要求（strict）补全记忆维护；连续触发不重复骚扰；对无变更会话零感知。

#### B2. `check` 分级：warn / strict / CI 模式

**为什么**：当前 `check` 只有"通过/失败"。作为门禁需要分级，作为团队协作需要 CI 可用。

**设计要点**：
- `check --warn`：只打印问题不返回非零（供 remind 模式和日常使用）。
- `check --strict`：现行为 + `--require-records-for-git-changes`，供 hook strict 模式和 CI。
- 输出机器可读格式 `--format json`（供 hook 和未来工具消费）。
- 提供 GitHub Actions 示例 workflow（放 `docs/ci/`）：PR 中若有代码变更但无记忆变更则评论提醒（不阻塞合并，团队可自行升级为必需检查）。

#### B3. 萃取质量规约（prompt 资产的打磨）

**为什么**：CLI 只保证格式，记忆值不值钱取决于 agent 萃取业务事实的质量。**本项目的护城河是 `references/` 里的萃取规则，不是 Python 脚本。**

**设计要点**：
- 在 `references/` 新增 `extraction-quality.md`：
  - maintain 前五问自检：① 用户最初的业务动机是什么（不是技术描述）？② 哪条业务规则从什么变成了什么？③ 出现了哪些用户特有术语？④ 用户否定过什么？⑤ 这条记忆能让半年后的新会话少问用户哪个问题？
  - 反模式清单：把 diff 描述当业务变化；把技术重构写成业务规则；把猜测写进 business-context；一次 maintain 塞多个不相关任务；标题写成"修改了 XX 文件"。
  - 好/坏记录对照示例各 2 条（用现有的"设计单两级审核"示例扩写）。
- SKILL.md 的 Workflow 中加入"写入前过一遍自检清单"的强制步骤。

#### B4. 冲突检测（轻量版）

**为什么**：business-context 是"当前真相"，新事实落地时旧条目可能已失效。真相层出现自相矛盾比没有记忆更糟。

**设计要点**：
- `maintain --business-change` 时，对目标 domain 文件做关键词重叠扫描；重叠度高的既有条目打印"可能与本次变更冲突，请确认是否标注 superseded"。
- 只提示、不自动改（保持工具克制，判断留给 agent 和人）。
- domain 条目支持 `~~已由 [任务] 取代~~` 的标注约定，写入 `references/memory-promotion-rules.md`。

### 主线 C：记忆质量与规模 —— 记录多了之后依然好用

#### C1. 路由打分 v2（维持零依赖）

**为什么**：当前是子串匹配 + 类型固定加分。记录上几百条后，路由不准会让"最小上下文"变成"错误上下文"。

**设计要点**（全部 stdlib 可实现）：
- memory-map 行结构化解析（按列取值，不再对整行做子串匹配）。
- 打分改为：词级匹配（中文按 2-gram 切分 + 英文按词）、词频逆文档频率式加权（罕见词命中权重高于"任务/变更"这类高频词）、领域列命中加权、时间衰减（近期记录小幅加分）、`business-context` 类型维持优先。
- 输出按预算截断：默认返回 ≤ 12 条且注明"先读前 3 条"。
- 打分函数独立成纯函数并补单测（给未来向量化留可替换接口，但**v1 阶段明确不做向量化**——零依赖红线优先）。

#### C2. 记忆生命周期：archive / supersede / compact

**为什么**：不可变记录只增不减，三年后 memory-map 会有上千行。需要"瘦身但不丢历史"的机制。

**设计要点**：
- `fengchao archive --before YYYY-MM-DD`：把早于指定日期的 task/changelog/plan/conversation 记录移入各目录 `archive/` 子目录，索引和 memory-map 中对应行改写为归档链接（链接不断，check 仍通过）。
- plan 记录状态流转：`fengchao plan-status <记录> --status implemented --link <task记录>`，落地后回填链接（当前模板里"后续落地链接：待补充"没有配套命令）。
- `fengchao compact`：重建 memory-map——去重、按类型和时间重排、归档行折叠到独立段落。

#### C3. 记忆迁移与体检

- `fengchao doctor`：status 的深度版——检测老布局、模板版本漂移、孤儿记录（不在任何索引中的文件）、索引中的死行，给出修复建议（只建议不自动改）。
- `fengchao migrate`：老布局（六目录散根下）→ 新布局（单一记忆根）的一键迁移，自动改写所有相对链接并跑 check 验证。

### 主线 D：开源工程成熟度

#### D1. 模板单一事实源

**为什么**：`fengchao.py` 内联字符串 / `templates/` / `adapters/` 三处并存且已不一致，人工同步必然失败。

**设计要点**：
- 确立 **`fengchao.py` 内联模板为唯一事实源**（保住"单文件可复制"的优点）。
- 新增开发者命令 `fengchao export-templates --out <dir>`，从内联模板生成 `templates/` 和 `adapters/` 的全部内容。
- 仓库里的 `templates/`、`adapters/` 变为生成产物，文件头注明"由 export-templates 生成，勿手改"。
- CI 加校验步骤：`export-templates` 到临时目录后 diff 仓库副本，不一致则失败。

#### D2. 版本化与升级

- `fengchao.py` 增加 `__version__`；`init` 把版本写入 `config.yaml`（`installed_version`）。
- `fengchao upgrade`：用当前 CLI 版本重写 `.fengchao/skill/`、薄入口和 marker 块，**绝不触碰记忆根**；升级前打印版本差和将重写的文件清单。
- `status`/`doctor` 显示版本漂移。

#### D3. 双语模板

- `language: en` 时全部生成物走英文模板集（内联模板函数按 language 分派）。
- 测试矩阵覆盖 zh-CN 和 en 两套断言。
- 注意：现有测试断言大量依赖中文文案，做双语时同步重构测试为按 language 参数化。

#### D4. 发布渠道与零依赖红线

- PyPI 发包（包名建议 `fengchao`，console script `fengchao`），零依赖使得 `uvx fengchao init` / `pipx run fengchao init` 开箱即用——这是目标安装路径（见第四部分）。
- 保留 git clone + `python3 scripts/fengchao.py` 的原始路径（无 Python 包管理器环境的兜底）。
- **红线**：运行时零第三方依赖永不破坏；永不加遥测（OpenSpec 有遥测需环境变量关闭，我们把"零遥测"写进 README 作为信任声明）。

#### D5. CI 与测试

- GitHub Actions：Python 3.9–3.13 矩阵跑 unittest + export-templates 同步校验 + 在临时目录跑一遍 init→plan→conversation→maintain→check 全流程冒烟。
- 新功能一律配端到端测试（延续现有 subprocess 风格，不引入 mock）。

---

## 第三部分：开发路线图

> 原则：先把"侵入性"降下来（M1），再把"可靠性"立起来（M2），然后解决"规模"（M3），最后"发布"（M4）。M1 是其他一切的地基——布局不定，hook 路径、教程、发布全都会返工。

### M1：低侵入安装与生命周期（地基）

| # | 任务 | 涉及 | 验收 |
|---|------|------|------|
| 1.1 | 新布局实现：`.fengchao/skill/` 单副本 + `memory_root` 单一记忆根 | `fengchao.py` init/load_config | init 后新增顶层目录 ≤ 2 |
| 1.2 | 薄入口生成（5 个 agent surface），`--agents` 参数 + 目录探测 | `fengchao.py` | 各 agent 仍能发现并使用 skill |
| 1.3 | CLAUDE.md 等宿主文件全部 marker 块化（A3） | `fengchao.py` | 已有文件原内容零改动 |
| 1.4 | `disable` / `enable` / `uninstall` / `status` 四命令（A2） | `fengchao.py` | disable→enable 逐字节还原；uninstall 不碰记忆 |
| 1.5 | `migrate`（老布局迁移） | `fengchao.py` | 迁移后 check 通过 |
| 1.6 | 全部新行为的端到端测试 | `tests/` | 通过 |
| 1.7 | export-templates + CI 同步校验（D1、D5 前置） | `fengchao.py`、`.github/workflows/` | CI 绿 |

**里程碑验收（Definition of Done）**：在一个已有 CLAUDE.md 和 .cursor 规则的真实项目上，`init → 使用 → disable → enable → uninstall` 全程 git diff 可读、可逆、无残留。

### M2：可靠性内核（核心卖点）

| # | 任务 | 涉及 | 验收 |
|---|------|------|------|
| 2.1 | `hook session-start` / `hook stop-gate` 子命令 + settings.json 注册/摘除 | `fengchao.py` | 见 B1 验收标准 |
| 2.2 | `hook_mode` 配置（remind/strict/off）+ 会话级防重 | `fengchao.py`、config | 同会话不重复提醒 |
| 2.3 | `check --warn` / `--strict` / `--format json`（B2） | `fengchao.py` | hook 与 CI 均可消费 |
| 2.4 | `references/extraction-quality.md` + SKILL.md 自检步骤（B3） | `references/` | 含五问清单、反模式、好坏示例 |
| 2.5 | maintain 冲突提示（B4） | `fengchao.py` | 命中时打印候选冲突条目 |
| 2.6 | git pre-commit 可选钩子 | `fengchao.py` | 默认不装，装后可干净卸载 |
| 2.7 | GitHub Actions 示例 workflow | `docs/ci/` | 可直接复制使用 |

**里程碑验收**：关闭所有人工提醒，仅靠 hooks，在 Claude Code 中完成一次真实开发后记忆维护自动发生；空跑会话零打扰。

### M3：规模与生命周期

| # | 任务 | 涉及 | 验收 |
|---|------|------|------|
| 3.1 | 路由打分 v2（C1），打分纯函数 + 单测 | `fengchao.py`、`tests/` | 构造 100+ 行 memory-map 的路由测试集，Top-3 命中率显著优于 v1 |
| 3.2 | `archive` / `compact`（C2） | `fengchao.py` | 归档后 check 通过、链接不断 |
| 3.3 | `plan-status` 回填命令（C2） | `fengchao.py` | plan→task 链接闭环 |
| 3.4 | `doctor`（C3） | `fengchao.py` | 能检出孤儿记录和死行 |
| 3.5 | `upgrade` + 版本化（D2） | `fengchao.py` | 升级不碰记忆根 |

### M4：开源发布

| # | 任务 | 涉及 | 验收 |
|---|------|------|------|
| 4.1 | 英文模板集 + 测试参数化（D3） | `fengchao.py`、`tests/` | zh/en 双矩阵绿 |
| 4.2 | README 重写（按第四部分教程草案）+ 差异化叙事（1.3 的定位表） | `README.md` | 60 秒内看懂"是什么、怎么装、怎么停" |
| 4.3 | PyPI 打包发布，`uvx fengchao init` 可用（D4） | `pyproject.toml` | 干净机器实测 |
| 4.4 | 示例项目 + 终端演示动图 | `examples/` | init→开发→自动维护→路由 完整演示 |
| 4.5 | CONTRIBUTING.md、LICENSE、issue 模板 | 仓库根 | — |
| 4.6 | 本文档更新为实际状态（蓝图 → 现状） | `docs/DESIGN.md` | — |

**发布判据**：一个从未接触过本项目的开发者，只看 README，能在 5 分钟内完成安装并跑通第一次 maintain；能在 1 分钟内完成停用。

---

## 第四部分：安装与使用设计（开源后的教程与最佳实践）

### 4.1 精品工具安装流程调研

| 工具 | 安装 | 初始化 | 升级 | 卸载 |
|------|------|--------|------|------|
| GitHub Spec Kit | `uv tool install specify-cli --from git+…`（uv/pipx） | `specify init .`，交互选 agent，探测 agent CLI 是否已装；支持已有项目 `--here --force` | `specify self check` / `self upgrade` | **未文档化** |
| OpenSpec | `npm install -g @fission-ai/openspec` | `openspec init` 交互式选 AI 工具 | 升级包 + `openspec update` 刷新注入的指令 | **未文档化**（仅遥测可关） |
| Cline Memory Bank | 无安装（复制 prompt 文件） | 手工放文件 | 手工 | 删文件 |
| husky / pre-commit（参照系） | 包管理器 | 一条命令注册 hook | 包升级 | 一条命令摘除 hook |
| shadcn/ui（参照系） | 无运行时依赖 | 代码复制进项目，产物归用户所有 | 重新生成 | 删文件即可 |

**提炼出的七条安装设计原则**（FengChao 全部采纳）：

1. **一条命令起步**，最好免安装（`uvx` 一次性运行 > 全局安装）。
2. **交互式选择 agent surface**，并用目录探测给默认值；非交互环境有合理缺省。
3. **产物全部可见、可 diff、可 review**——写进用户项目的每个字节都应出现在 git diff 里。
4. **产物归用户所有**（shadcn 哲学）：记忆数据是用户的文档，工具死了数据还活着。
5. **升级与数据分离**：升级只动工具本体，永不动用户数据。
6. **卸载与安装对称**：装了什么就能干净摘除什么——这是 OpenSpec/Spec Kit 都没做的，FengChao 要把它做成卖点。
7. **零遥测、零网络请求**，把信任写进文档。

### 4.2 目标安装体验（未来 README 的核心承诺）

```bash
# 引入（免安装，60 秒）
cd your-project
uvx fengchao init            # 交互选择 agent；或 --agents claude,cursor

# 从此不用管。AI 会话会：
#   - 新会话自动从 fengwang 路由回业务记忆
#   - 真实开发交付后自动沉淀 task-record + changelog
#   - 用户解释业务时自动萃取 conversation-record

# 想看看它在干什么
uvx fengchao status

# 想暂停（保留一切，随时恢复）
uvx fengchao disable

# 想彻底移除工具（记忆文档保留，属于你）
uvx fengchao uninstall
```

### 4.3 使用教程草案（未来 README 骨架）

**① 60 秒 Quick Start**
- 一条 init 命令 + 一张"init 写入了什么"清单表（透明是信任的基础）。
- 立刻可验证：`fengchao status` 看到全绿。

**② 日常使用：你什么都不用做**
- 明确告诉用户"正常开发即可"：路由和维护由 skill 规则 + hooks 驱动。
- 唯二建议的人工动作：a) 重要业务解释后可以说一句"把这个记入业务记忆"；b) 偶尔 `fengchao status` 体检。

**③ 团队协作最佳实践**
- 记忆根默认入 git：业务记忆是团队资产，PR 里 review 记忆变更就像 review 代码。
- 建议约定：带业务规则变化的 PR 应包含对应 task-record（用 docs/ci 的 workflow 自动提醒）。
- 新成员 onboarding：读 `fengchao/FENGWANG.md` + `business-context/CONTEXT-INDEX.md` 即可接手业务上下文——这本身就是卖点。

**④ 停用与卸载**
- 三级操作明确分开讲：disable（暂停）/ uninstall（移除工具）/ `--purge-memory`（删数据，二次确认）。
- 强调：即使卸载，记忆仍是一套完好的、人类可读的 Markdown 文档库。

**⑤ FAQ（预置）**
- 会不会拖慢我的 AI 会话？（路由是最小集合；hook < 500ms；无网络请求）
- 记忆会不会泄露对话隐私？（默认 summary-only，永不存完整对话）
- 和 OpenSpec / Spec Kit 冲突吗？（不冲突，管的是不同生命周期，可共存）
- 不用 Claude Code 能用吗？（能，五个 surface + git hook 兜底，效果分级说明）

---

## 第五部分：设计红线（任何后续开发不可违背）

1. **运行时零第三方依赖**：`fengchao.py` 只用 Python 标准库。
2. **存储只用 Markdown + Git**：不引入数据库、不引入向量存储、不做云端。
3. **Agent 中立**：核心逻辑不绑定任何单一 AI 工具；Claude Code 只是 hook 能力的第一优先实现。
4. **隐私默认**：summary-only，永不存完整对话；零遥测、零网络请求。
5. **用户记忆数据神圣**：任何命令（uninstall/upgrade/migrate/compact）都不得在无显式确认下删除或改写记忆内容本身。
6. **卸载对称性**：每一个写入用户项目的字节，都必须有对应的干净摘除路径。
7. **写入触发边界**：只有真实开发交付才写证据层——这条业务规则高于任何"自动化便利"。
8. **克制**：工具只保证格式、校验与提醒；业务判断永远留给 agent 和人。

---

## 附录：术语表

| 术语 | 含义 |
|------|------|
| 蜂巢（FengChao） | 本项目：项目业务记忆的整体系统 |
| 蜂王（FengWang） | 记忆路由入口：FENGWANG.md + memory-map.md + `fengwang --query` |
| 业务真相（business truth） | 已落地、经证据支撑的当前业务事实，存于 business-context |
| 证据层 | task-records + changelog：不可变的交付证据 |
| 参考层 | plan-records + conversation-records：历史/上下文记忆，默认不是真相 |
| 提升（promotion） | 参考层信息经确认/落地后进入 business-context 的过程 |
| 否定记忆 | 用户明确拒绝过的方案的记录，防止 AI 重复提议 |
| 薄入口 | 放在各 agent 目录下、仅指向 `.fengchao/skill/` 的最小文件 |
| marker 块 | `<!-- FENGCHAO-BUSINESS-MEMORY:START/END -->` 包裹的注入内容，保证可干净摘除 |
| 硬门禁 | 通过 hooks / check 强制记忆维护发生的机制，区别于 prompt 软约定 |
