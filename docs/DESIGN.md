# FengChaoSkills 产品设计与开发总体规划

> 版本：v1.3
> 日期：2026-07-09
> 性质：本文档是 FengChaoSkills 从 demo 走向成熟开源项目的总设计文档。任何后续开发者应先读本文档，再读 `CLAUDE.md` 和 `skills/fengchao-business-memory/` 下的规则文件。
> 读者：项目维护者、后续参与开发的工程师、（部分章节）未来的开源贡献者。

**修订记录**

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07-07 | 蓝图初版：项目理解、四条产品主线、M1–M4 路线图、安装设计 |
| v1.1 | 2026-07-07 | 合并 OpenSpec 专项调研结论：新增 B4 真相层 delta 语义合并（替代原冲突检测方案）、B5 maintain 分档、A4 薄命令、B2 升级为 agent 契约、C1 增加预算管制、M1 增加 dogfooding；新增第六部分借鉴决议、附录 B 规则条目格式规范、附录 C 诊断契约；新增红线 9 |
| v1.2 | 2026-07-09 | 蓝图 → 现状：M1–M4 全部开发任务已实现并通过测试（v0.2.0），新增第七部分实施状态；1.6 的现状盘点保留作为历史记录，其所列缺失项均已解决 |
| v1.3 | 2026-07-09 | R2 核查：PyPI 名 `fengchao` 已被占用，包名与 console script 定为 `fengchao-skills`（决策记录见 release-plan.md 第 10 条），同步 D4 与 4.2/4.4 的安装命令 |

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
- **真相层追加即腐化**：`update_domain_context()` 是纯追加。同一条业务规则改三次，domain 文件里三个版本并存，"当前真相"退化成历史日志——直接违背 1.4 原则 1。这是 demo 最严重的设计债，解法见 B4。
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
- 新增 `init --memory-only`：只创建记忆脚手架和 config，不装 skill 副本、不写任何宿主注入。两个用途：① 用户只想要记忆结构、自己管 agent 规则；② 本仓库 dogfooding（源码仓库自身不需要 skill 副本，见 M1 任务 1.8）。

**验收标准**：`init` 后目标项目新增顶层可见目录 ≤ 2 个（`.fengchao/` + 记忆根）；skill 正文在目标项目中只存在一份。

#### A2. 生命周期命令：`enable` / `disable` / `uninstall` / `status`

**为什么**：用户要求"想停用也能非常轻松地停用"。停用 ≠ 卸载 ≠ 删数据，三者必须分离。

**命令设计**：

| 命令 | 行为 | 不动什么 |
|------|------|----------|
| `fengchao disable` | 摘除 CLAUDE.md/AGENTS.md 中的 marker 块、删除各 agent 薄入口/薄命令/rule 文件、移除 hook 注册；在 config 写 `enabled: false` | 记忆数据、`.fengchao/` 本体全部保留 |
| `fengchao enable` | disable 的精确逆操作 | — |
| `fengchao uninstall` | disable + 删除 `.fengchao/`；打印记忆根位置并明确告知"记忆数据已保留" | **永不自动删除记忆根**；`--purge-memory` 需要交互式二次确认才删 |
| `fengchao status` | 显示：版本、启用状态、已接入的 agent、记忆根位置、各层记录数、最近一条记录日期、check 健康度 | 只读 |

**验收标准**：`disable` 后 `git diff` 干净可读（只有 marker 块和薄文件消失）；`disable && enable` 后项目与之前逐字节一致；`uninstall` 默认绝不触碰记忆数据。

#### A3. 所有写入宿主文件的内容一律 marker 块化

**为什么**：当前 `AGENTS.md` 用 marker 追加（对），但 `CLAUDE.md` 是 `write_if_missing` 整文件（用户已有 CLAUDE.md 时静默跳过，行为不一致，且无法干净移除）；`opencode.json` 直接整文件创建。

**设计要点**：
- 统一规则：凡写入用户已有/可能已有的文件（CLAUDE.md、AGENTS.md），一律以 `<!-- FENGCHAO-BUSINESS-MEMORY:START/END -->` 包裹追加；文件不存在则创建后追加。
- `opencode.json` 若已存在则不覆盖，改为打印手工合并指引（JSON 无注释语法，无法安全 marker 化，宁可不动用户文件）。
- marker 块内容尽量短（≤ 15 行）：只写触发边界 + "读 `.fengchao/skill/SKILL.md`"，细则全部留在 skill 内部。宿主文件里的字越少，侵入感越低。

**验收标准**：对已有 CLAUDE.md/AGENTS.md/opencode.json 的项目执行 `init`，用户原内容一字不动；`disable` 能精确摘除全部注入。

#### A4. 薄命令：给用户三个主动动词（引擎-方向盘分离）

**为什么**：借鉴 OpenSpec 的"CLI 是引擎、斜杠命令是方向盘"架构（决议见第六部分）。目前 FengChao 只有被动触发（规则注入 + 未来的 hook），用户想主动使用时没有入口。但必须克制——OpenSpec 有十几个命令，我们的"不打扰"定位决定动词 **≤ 3 个**。

**三个动词**：

| 动词 | 意图 | 命令文件内容要点 |
|------|------|------------------|
| `/fengchao:route` | 手动路由："帮我找回这个需求相关的业务记忆" | 运行 `fengwang --query "<用户输入>"`，读取返回的记录文件，汇报要点 |
| `/fengchao:remember` | 主动记忆："把刚才的解释记入业务记忆" | 按 conversation capture 模式萃取当前对话，走 `conversation` 子命令 |
| `/fengchao:status` | 体检："业务记忆现在什么状态" | 运行 `status`，向用户解读输出 |

**设计要点**：
- 每个命令文件 ≤ 10 行：frontmatter + 一句意图说明 + "执行 `python3 .fengchao/skill/scripts/fengchao.py <子命令>` 并遵循 `.fengchao/skill/SKILL.md`"。命令文件是薄的，逻辑全在引擎里。
- 路径映射维护在 `fengchao.py` 的单一常量 `AGENT_COMMAND_PATHS` 中。Claude Code 路径确定为 `.claude/commands/fengchao/<verb>.md`（呈现为 `/fengchao:<verb>`）；Cursor/Codex/OpenCode 的命令目录约定**在 M1 落地时逐一核实最新事实再写入**（各工具约定变动快，文档不预先猜测）。核实结果直接记录为 `AGENT_COMMAND_PATHS` 的注释。
- 薄命令随 `init` 按所选 agent 生成，随 `disable` 对称摘除（纳入 A2 的验收范围）。

**验收标准**：在 Claude Code 中输入 `/fengchao:route 审核流程` 能得到路由结果；`disable` 后三个命令消失无残留。

### 主线 B：可靠性 —— 让记忆维护"必然发生"而且"写得正确"

> 这是产品成败的最大风险点。结构设计再好，agent 不执行维护动作就一切归零（B1、B2）；执行了但写入方式错误，真相层会腐化（B4、B5）。

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

#### B2. Agent 契约：诊断信封 + 退出码 + `--format json`

**为什么**：hook、CI 和 agent 消费 CLI 输出时，人读文本是不可靠接口。借鉴 OpenSpec 的 agent contract（决议见第六部分）：机器可读的诊断信封，且诊断自带修复建议（`fix` 字段），agent 拿到就能直接行动。

**设计要点**：
- 所有校验/合并类子命令支持 `--format json`（M2 范围先做 `check`、`fengwang`、`status`、`maintain` 的错误输出）。
- 统一诊断信封与退出码契约，**具体 schema、code 枚举、退出码表见附录 C**——实现时以附录 C 为准，新增诊断必须先在附录 C 登记 code。
- `check` 分级：
  - `check --warn`：只打印问题，退出码恒为 0（供 hook remind 模式和日常使用）；
  - `check --strict`：现行为 + `--require-records-for-git-changes`（供 hook strict 模式和 CI）。
- 提供 GitHub Actions 示例 workflow（放 `docs/ci/`）：PR 中若有代码变更但无记忆变更则评论提醒（不阻塞合并，团队可自行升级为必需检查）。

**验收标准**：`check --format json` 输出可被 `python -m json.tool` 解析；每条诊断都有登记在册的 code 和可执行的 fix 建议；退出码符合附录 C 契约。

#### B3. 萃取质量规约（prompt 资产的打磨）

**为什么**：CLI 只保证格式，记忆值不值钱取决于 agent 萃取业务事实的质量。**本项目的护城河是 `references/` 里的萃取规则，不是 Python 脚本。**

**设计要点**：
- 在 `references/` 新增 `extraction-quality.md`：
  - maintain 前五问自检：① 用户最初的业务动机是什么（不是技术描述）？② 哪条业务规则从什么变成了什么？③ 出现了哪些用户特有术语？④ 用户否定过什么？⑤ 这条记忆能让半年后的新会话少问用户哪个问题？
  - **change-kind 判定步骤**（配合 B4）：写入业务变化前，必须先读目标 domain 文件的"当前业务规则"段，判定本次是 `added`（全新规则）/ `modified`（改既有规则，找到对应规则名）/ `removed`（废除既有规则），并选定或复用稳定规则名。
  - 反模式清单：把 diff 描述当业务变化；把技术重构写成业务规则；把猜测写进 business-context；一次 maintain 塞多个不相关任务；标题写成"修改了 XX 文件"；modified 时不查规则名直接 added 造成重复条目。
  - 好/坏记录对照示例各 2 条（用现有的"设计单两级审核"示例扩写）。
- SKILL.md 的 Workflow 中加入"写入前过一遍自检清单 + change-kind 判定"的强制步骤。

#### B4. 真相层 delta 语义合并（v1.1 核心升级，替代原"冲突检测"方案）

**为什么**：1.6 指出的最严重设计债——`update_domain_context()` 纯追加，同一规则多次变更后多版本并存，真相层退化成日志。OpenSpec 的 delta+merge（ADDED/MODIFIED/REMOVED 归档时合并进主 spec）是对这个问题最成熟的工程答案。原 v1.0 的"冲突检测（只提示）"方案废弃：与其事后检测冲突，不如让写入动作本身携带语义。

**规则条目与稳定 key**：business-context 的 domain 文件中，每条业务规则是一个结构化条目，以规则名为稳定 key。**条目格式规范见附录 B**，要点：一个条目 = 一个可观察业务事实 + 一个具体场景 + 来源链接。

**CLI 参数设计**（`maintain` 新增）：

```bash
fengchao maintain \
  --title "..." --summary "..." --implementation "..." \
  --business-change "设计单最终通过必须依次经过主管审核和经理审核。" \
  --change-kind modified \            # added | modified | removed，默认 added
  --rule-name "设计单审核流程" \       # 稳定 key；提供 --business-change 时必填
  --scenario "设计师提交后，主管一审通过、经理二审通过才进入已通过状态；任一级驳回整单退回。"
```

**合并算法 `merge_domain_rule()`**（替代 `update_domain_context()`）：

1. 解析目标 domain 文件"## 当前业务规则"段下所有 `### 规则：<名>` 块。
2. 按 `--change-kind` 分派：
   - **added**：规则名已存在 → 整个 maintain 失败退出（诊断 `rule_already_exists`，fix："改用 --change-kind modified；或确认是新规则后换名"）。不存在 → 按附录 B 格式追加条目。
   - **modified**：规则名不存在 → 失败退出（诊断 `rule_not_found`，输出现有规则名清单和最相近候选，fix："核对规则名，或改用 added"）。存在 → **整块替换**为新内容；新条目的"沿革"行 = 旧条目的"来源"链接 + 旧"沿革"行（保链不保文——旧规则原文本来就在不可变的旧 task-record 里，真相层不需要保留）。
   - **removed**：规则名不存在 → 同 modified 报错。存在 → 从"当前业务规则"段移除整块，在"## 已废除规则"段追加一行：`- ~~<规则名>~~：YYYY-MM-DD 由 [任务](链接) 废除`。
3. 失败即整体失败：maintain 在合并失败时不得写入 task-record/changelog（先合并后落盘，或落盘后回滚——实现取先验证后写入的顺序），避免半成品状态。
4. 合并完成后自动跑 `check`。

**配套改动**：
- `domain_template()` 改造：明确"## 当前业务规则"（结构化条目）与"## 已废除规则"两个段。
- 老式追加条目（"## 日期 已落地业务事实"）：`doctor` 检出并列出，建议人工整理为规则条目；**不做自动转换**（内容语义机器拿不准，遵守红线 8"克制"）。
- 术语/坑点/否定记忆**不采用**规则条目格式——它们不是行为契约，留在 conversation-records 和 debt-registry 的既有格式里。

**验收标准**：对同一 `--rule-name` 依次执行 added → modified → modified，domain 文件中该规则**始终只有一个现行条目**，沿革链接完整可追；removed 后条目出现在废除段；错误的 change-kind 组合全部按契约报错且不留半成品。

#### B5. maintain 分档：lite / full（渐进严格度）

**为什么**：借鉴 OpenSpec 的 Lite/Full mode（防止 AI 过度仪式化）。不是每次交付都值得完整仪式——纯 bugfix、重构、杂务写满一套 task-record 是噪音，噪音多了 agent 和人都会开始忽略记忆系统。

**分档设计**：

| 档位 | 判定 | 写入 |
|------|------|------|
| **full** | 提供了 `--business-change`（有业务含义的交付） | task-record + changelog + B4 合并 + memory-map（现有完整流程） |
| **lite** | 未提供 `--business-change` | 仅 changelog + memory-map 行；**不写 task-record**，不动 business-context |

- 逃生舱：`--with-task-record` 允许 lite 交付强制写 task-record（例如重大重构虽无业务变化但值得留档）。
- 给 agent 的一句话判定标准（写入 `references/lifecycle.md`）："**半年后的新会话是否需要知道这次改动的'为什么'？** 需要 → full；不需要（纯修复/重构/杂务）→ lite。"
- 向后兼容注意：现行为是无 `--business-change` 也写 task-record，测试断言需同步修改。

**验收标准**：lite 交付产生且仅产生一条 changelog 和一行 memory-map；full 交付走完整链路；`check --strict` 对 lite 交付不误报"缺 task-record"（校验规则同步放宽为"有 changelog 即可"）。

### 主线 C：记忆质量与规模 —— 记录多了之后依然好用

#### C1. 路由打分 v2 + 预算管制（维持零依赖）

**为什么**：当前是子串匹配 + 类型固定加分。记录上几百条后，路由不准会让"最小上下文"变成"错误上下文"。同时借鉴 OpenSpec 的容量管制思想：不是"尽量少读"，而是"量化上限 + 超限可见"。

**打分设计要点**（全部 stdlib 可实现）：
- memory-map 行结构化解析（按列取值，不再对整行做子串匹配）。
- 打分改为：词级匹配（中文按 2-gram 切分 + 英文按词）、词频逆文档频率式加权（罕见词命中权重高于"任务/变更"这类高频词）、领域列命中加权、时间衰减（近期记录小幅加分）、`business-context` 类型维持优先。
- 打分函数独立成纯函数并补单测（给未来向量化留可替换接口，但**v1 阶段明确不做向量化**——零依赖红线优先）。

**预算管制要点**：
- `fengwang --query` 输出设字节预算（默认 4KB 文本），超限截断并打印 `(已截断：还有 N 条低分匹配，请细化查询词)`；
- 输出按预算截断且注明"先读前 3 条"；FENGWANG.md 模板同步写入"路由结果先读前 3 条"的约定；
- memory-map 单行 keywords 列 ≤ 120 字符（`collect_keywords` 现有 20 词上限之外再加字符上限），`check` 对超长行发 `memory_map_row_too_long` 警告。

**验收标准**：构造 100+ 行 memory-map 的路由测试集，Top-3 命中率显著优于 v1；任意查询输出 ≤ 预算上限。

#### C2. 记忆生命周期：archive / supersede / compact

**为什么**：不可变记录只增不减，三年后 memory-map 会有上千行。需要"瘦身但不丢历史"的机制。

**设计要点**：
- `fengchao archive --before YYYY-MM-DD`：把早于指定日期的 task/changelog/plan/conversation 记录移入各目录 `archive/` 子目录，索引和 memory-map 中对应行改写为归档链接（链接不断，check 仍通过）。
- plan 记录状态流转：`fengchao plan-status <记录> --status implemented --link <task记录>`，落地后回填链接（当前模板里"后续落地链接：待补充"没有配套命令）。
- `fengchao compact`：重建 memory-map——去重、按类型和时间重排、归档行折叠到独立段落。

#### C3. 记忆迁移与体检

- `fengchao doctor`：status 的深度版——检测老布局、模板版本漂移、孤儿记录（不在任何索引中的文件）、索引中的死行、老式追加条目（见 B4）、超长 memory-map 行，给出修复建议（只建议不自动改）。
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
- `fengchao upgrade`：用当前 CLI 版本重写 `.fengchao/skill/`、薄入口、薄命令和 marker 块，**绝不触碰记忆根**；升级前打印版本差和将重写的文件清单。
- `status`/`doctor` 显示版本漂移。

#### D3. 双语模板

- `language: en` 时全部生成物走英文模板集（内联模板函数按 language 分派）。
- 测试矩阵覆盖 zh-CN 和 en 两套断言。
- 注意：现有测试断言大量依赖中文文案，做双语时同步重构测试为按 language 参数化。

#### D4. 发布渠道与零依赖红线

- PyPI 发包（包名与 console script 均为 `fengchao-skills`——原建议名 `fengchao` 在 PyPI 已被活跃包占用，2026-07-09 核查确定，见 release-plan.md 决策 10），零依赖使得 `uvx fengchao-skills init` / `pipx run fengchao-skills init` 开箱即用——这是目标安装路径（见第四部分）。
- 保留 git clone + `python3 scripts/fengchao.py` 的原始路径（无 Python 包管理器环境的兜底）。
- **红线**：运行时零第三方依赖永不破坏；永不加遥测（OpenSpec 有遥测需环境变量关闭，我们把"零遥测"写进 README 作为信任声明）。

#### D5. CI 与测试

- GitHub Actions：Python 3.9–3.13 矩阵跑 unittest + export-templates 同步校验 + 在临时目录跑一遍 init→plan→conversation→maintain→check 全流程冒烟。
- 新功能一律配端到端测试（延续现有 subprocess 风格，不引入 mock）。

---

## 第三部分：开发路线图

> 原则：先把"侵入性"降下来（M1），再把"可靠性"立起来（M2），然后解决"规模"（M3），最后"发布"（M4）。M1 是其他一切的地基——布局不定，hook 路径、教程、发布全都会返工。
> 从 M1 第一个任务起开始 dogfooding（任务 1.8）：本仓库的每次交付都用 FengChao 自己记录。

### M1：低侵入安装与生命周期（地基）

| # | 任务 | 涉及 | 验收 |
|---|------|------|------|
| 1.1 | 新布局实现：`.fengchao/skill/` 单副本 + `memory_root` 单一记忆根 | `fengchao.py` init/load_config | init 后新增顶层目录 ≤ 2 |
| 1.2 | 薄入口生成（5 个 agent surface）+ 薄命令生成（A4 三动词），`--agents` 参数 + 目录探测；核实各工具命令目录约定并写入 `AGENT_COMMAND_PATHS` | `fengchao.py` | 各 agent 能发现 skill；Claude Code 三命令可用 |
| 1.3 | CLAUDE.md 等宿主文件全部 marker 块化（A3） | `fengchao.py` | 已有文件原内容零改动 |
| 1.4 | `disable` / `enable` / `uninstall` / `status` 四命令（A2），含薄命令的对称摘除 | `fengchao.py` | disable→enable 逐字节还原；uninstall 不碰记忆 |
| 1.5 | `migrate`（老布局迁移） | `fengchao.py` | 迁移后 check 通过 |
| 1.6 | 全部新行为的端到端测试 | `tests/` | 通过 |
| 1.7 | export-templates + CI 同步校验（D1、D5 前置） | `fengchao.py`、`.github/workflows/` | CI 绿 |
| 1.8 | **Dogfooding 启动**：本仓库 `init --memory-only`，M1 各任务交付即用 `maintain` 记录，规划用 `plan` 记录 | 本仓库 | 仓库内出现真实记忆记录，作为活示例 |

**里程碑验收（Definition of Done）**：在一个已有 CLAUDE.md 和 .cursor 规则的真实项目上，`init → 使用 → disable → enable → uninstall` 全程 git diff 可读、可逆、无残留；本仓库 dogfooding 记录 ≥ 5 条。

### M2：可靠性内核（核心卖点）

| # | 任务 | 涉及 | 验收 |
|---|------|------|------|
| 2.1 | `hook session-start` / `hook stop-gate` 子命令 + settings.json 注册/摘除 | `fengchao.py` | 见 B1 验收标准 |
| 2.2 | `hook_mode` 配置（remind/strict/off）+ 会话级防重 | `fengchao.py`、config | 同会话不重复提醒 |
| 2.3 | Agent 契约落地：诊断信封 + 退出码 + `check/fengwang/status/maintain` 的 `--format json`（B2、附录 C） | `fengchao.py` | JSON 可解析；code 全部在附录 C 登记 |
| 2.4 | `references/extraction-quality.md`（五问自检 + change-kind 判定 + 反模式 + 好坏示例）+ SKILL.md 工作流更新（B3） | `references/` | 文档齐备且被 SKILL.md 引用 |
| 2.5 | **B4 delta 语义合并**：规则条目格式（附录 B）、`--change-kind/--rule-name/--scenario` 参数、`merge_domain_rule()`、domain 模板改造、先验证后写入 | `fengchao.py`、`references/`、`tests/` | 见 B4 验收标准 |
| 2.6 | **B5 maintain 分档**：lite/full 判定、`--with-task-record`、check 校验规则放宽、lifecycle.md 更新 | `fengchao.py`、`references/`、`tests/` | 见 B5 验收标准 |
| 2.7 | git pre-commit 可选钩子 | `fengchao.py` | 默认不装，装后可干净卸载 |
| 2.8 | GitHub Actions 示例 workflow | `docs/ci/` | 可直接复制使用 |

**里程碑验收**：① 关闭所有人工提醒，仅靠 hooks，在 Claude Code 中完成一次真实开发后记忆维护自动发生，空跑会话零打扰；② 对同一规则连续 added→modified→modified，domain 文件始终只有一个现行条目；③ lite 交付零 task-record 噪音。

### M3：规模与生命周期

| # | 任务 | 涉及 | 验收 |
|---|------|------|------|
| 3.1 | 路由打分 v2 + 预算管制（C1），打分纯函数 + 单测 | `fengchao.py`、`tests/` | 100+ 行 memory-map 测试集 Top-3 命中率显著优于 v1；输出 ≤ 预算 |
| 3.2 | `archive` / `compact`（C2） | `fengchao.py` | 归档后 check 通过、链接不断 |
| 3.3 | `plan-status` 回填命令（C2） | `fengchao.py` | plan→task 链接闭环 |
| 3.4 | `doctor`（C3，含老式追加条目与超长行检出） | `fengchao.py` | 能检出孤儿记录、死行、老式条目 |
| 3.5 | `upgrade` + 版本化（D2） | `fengchao.py` | 升级不碰记忆根 |

### M4：开源发布

| # | 任务 | 涉及 | 验收 |
|---|------|------|------|
| 4.1 | 英文模板集 + 测试参数化（D3） | `fengchao.py`、`tests/` | zh/en 双矩阵绿 |
| 4.2 | README 重写（按第四部分教程草案）+ 差异化叙事（1.3 的定位表） | `README.md` | 60 秒内看懂"是什么、怎么装、怎么停" |
| 4.3 | `docs/` 细分文档集（借鉴 OpenSpec 文档组织，初版 8 篇）：getting-started、concepts、glossary、faq、team-workflow、existing-projects（在已有大项目中引入）、troubleshooting、ci | `docs/` | 每篇单一主题、互相链接 |
| 4.4 | PyPI 打包发布，`uvx fengchao-skills init` 可用（D4） | `pyproject.toml` | 干净机器实测 |
| 4.5 | 示例项目 + 终端演示动图（可直接用本仓库 dogfooding 记录作素材） | `examples/` | init→开发→自动维护→路由 完整演示 |
| 4.6 | CONTRIBUTING.md、LICENSE、issue 模板 | 仓库根 | — |
| 4.7 | 本文档更新为实际状态（蓝图 → 现状） | `docs/DESIGN.md` | — |

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
uvx fengchao-skills init     # 交互选择 agent；或 --agents claude,cursor

# 从此不用管。AI 会话会：
#   - 新会话自动从 fengwang 路由回业务记忆
#   - 真实开发交付后自动沉淀 task-record + changelog
#   - 用户解释业务时自动萃取 conversation-record

# 想主动用（三个动词）
#   /fengchao:route     找回相关业务记忆
#   /fengchao:remember  把刚才的解释记入记忆
#   /fengchao:status    看看记忆系统状态

# 想看看它在干什么
uvx fengchao-skills status

# 想暂停（保留一切，随时恢复）
uvx fengchao-skills disable

# 想彻底移除工具（记忆文档保留，属于你）
uvx fengchao-skills uninstall
```

### 4.3 使用教程草案（未来 README 骨架）

**① 60 秒 Quick Start**
- 一条 init 命令 + 一张"init 写入了什么"清单表（透明是信任的基础）。
- 立刻可验证：`fengchao status` 看到全绿。

**② 日常使用：你什么都不用做**
- 明确告诉用户"正常开发即可"：路由和维护由 skill 规则 + hooks 驱动。
- 唯二建议的人工动作：a) 重要业务解释后说一句 `/fengchao:remember`；b) 偶尔 `fengchao status` 体检。

**③ 团队协作最佳实践**
- 记忆根默认入 git：业务记忆是团队资产，PR 里 review 记忆变更就像 review 代码。
- 建议约定：带业务规则变化的 PR 应包含对应 task-record（用 docs/ci 的 workflow 自动提醒）。
- 新成员 onboarding：读 `fengchao/FENGWANG.md` + `business-context/CONTEXT-INDEX.md` 即可接手业务上下文——这本身就是卖点。

**④ 停用与卸载**
- 三级操作明确分开讲：disable（暂停）/ uninstall（移除工具）/ `--purge-memory`（删数据，二次确认）。
- 强调：即使卸载，记忆仍是一套完好的、人类可读的 Markdown 文档库。

**⑤ FAQ（预置）**
- 会不会拖慢我的 AI 会话？（路由是最小集合且有字节预算；hook < 500ms；无网络请求）
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
9. **真相层唯一现行原则**：business-context 中同一规则名在同一时刻只能有一个现行条目；任何写入路径（maintain/migrate/未来功能）都必须经过 B4 的语义合并，禁止绕过合并直接追加规则。

---

## 第六部分：同类精品借鉴决议（OpenSpec 专项，2026-07-07）

> 本节记录对 OpenSpec 深度调研后的采纳/否决决定及理由，防止后续开发者重新争论已决策事项。调研依据：OpenSpec docs/concepts.md、writing-specs.md、agent-contract.md、how-commands-work.md 及其仓库结构。

### 采纳（7 项，均已落入本文档对应章节）

| # | OpenSpec 的设计 | 采纳理由 | 落点 |
|---|-----------------|----------|------|
| 1 | Delta 语义合并（ADDED/MODIFIED/REMOVED → 归档时合并进主 spec，specs 永远是当前真相） | 直接解决我们真相层"追加即腐化"的设计债（1.6）；与认识论分层完全兼容 | **B4**（核心升级）、红线 9、附录 B |
| 2 | 规则条目纪律：一条 Requirement = 一个可观察行为 + 稳定命名 + 可验证场景；"没看过代码的测试人员能否判断通过" | 稳定 key 是 delta 合并和防重复的锚点；场景让规则边界清晰 | **附录 B**（只用于规则条目，不套用于术语/坑/否定记忆） |
| 3 | Dogfooding（OpenSpec 仓库用 openspec/ 管理自身开发） | 最真实的测试 + 最有说服力的活示例，成本≈0 | **M1 任务 1.8**、A1 的 `--memory-only` |
| 4 | 引擎-方向盘分离（CLI 引擎 + 每工具生成对应格式的斜杠命令） | 补上"用户主动动词"的空缺；命令文件是薄的，逻辑在引擎 | **A4**（克制为 3 个动词） |
| 5 | 渐进披露的预算化（参考索引 50KB 上限 + truncated 警告；list 概览 / show 展开分层） | 我们已有三级披露直觉，缺的是"量化上限 + 超限可见" | **C1** 预算管制 |
| 6 | Lite/Full 渐进严格度（默认轻量，高风险才完整仪式） | 防止过度仪式化产生记忆噪音 | **B5** |
| 7 | Agent 契约（--json 单文档、诊断信封 {severity, code, message, fix}、退出码契约） | hook/CI/agent 消费需要机器可读接口；fix 字段让诊断可直接执行 | **B2**、附录 C |

### 否决（4 项）

| # | OpenSpec 的设计 | 否决理由 |
|---|-----------------|----------|
| 1 | "规范可执行、生成代码"的世界观 | 方向相反：我们是事后记账（业务认知生命周期），不是事前驱动（变更生命周期）；两者可共存不必融合 |
| 2 | 全套 RFC 2119 形式主义（MUST/SHALL/SHOULD/MAY 全文覆盖） | 业务记忆的大半内容（术语/偏好/坑/否定项）不是行为契约；强套会加重萃取负担、文本生硬。仅在附录 B 规则条目中保留"单句规则"纪律 |
| 3 | 重命令集（explore/propose/apply/ff/sync/archive/verify…十余个） | 与"不打扰"定位直接冲突；用户动词上限 3 个（A4） |
| 4 | JSON 结构化指令注入 + dependencies/unlocks 任务编排 | 那是为 spec 驱动的实现编排服务的；FengChao 不做任务编排，引入只会增重 |

---

## 第七部分：实施状态（v0.2.0，2026-07-09）

> 本节记录蓝图的实际落地情况。实现载体：`skills/fengchao-business-memory/scripts/fengchao.py`（单文件，`__version__ = "0.2.0"`）；测试：`tests/test_fengchao_cli.py`（36 个端到端 + 单元用例）；本仓库已按任务 1.8 开启 dogfooding（`fengchao/` 下 5 条 task-record + 1 条 implemented plan 即本次交付的活示例）。

### 里程碑完成状态

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| M1 低侵入安装与生命周期 | ✅ 全部完成 | 1.1–1.8 全部落地：单一安装点 + 单一记忆根、薄入口 + 三动词薄命令、marker 块化、disable/enable 逐字节可逆（有测试）、uninstall 不碰记忆、migrate、export-templates + CI 校验、dogfooding 启动 |
| M2 可靠性内核 | ✅ 全部完成 | 2.1–2.8 全部落地：session-start/stop-gate hooks + settings.json 注册摘除、hook_mode 三档 + 会话防重、诊断信封 + `--format json` + 退出码契约、extraction-quality.md、B4 语义合并（先验证后写入）、B5 lite/full、install-git-hook、docs/ci 示例 workflow |
| M3 规模与生命周期 | ✅ 全部完成 | 3.1–3.5 全部落地：打分 v2 纯函数 + 单测 + 4KB 预算、archive/compact、plan-status、doctor（孤儿/死行/老式条目/超长行）、upgrade + 版本化 |
| M4 开源发布 | ✅ 开发部分完成 | 4.1 双语模板 + 测试、4.2 README 重写、4.3 docs 八篇、4.4 pyproject 打包（本地 wheel 实测可用）、4.5 examples 演示脚本、4.6 CONTRIBUTING/LICENSE/issue 模板、4.7 本节。**遗留的非开发动作**（执行规划见 [release-plan.md](release-plan.md)）：GitHub 开源与 CI 首跑、PyPI 发布、种子用户测试、插件市场（后置）、演示动图录制 |

### A4 命令目录核实结果（2026-07-08，已写入 `AGENT_COMMAND_PATHS` 注释）

| 工具 | 项目级命令约定 | 处理 |
|------|----------------|------|
| Claude Code | `.claude/commands/fengchao/<verb>.md` → `/fengchao:<verb>` | 生成三动词 |
| Cursor | `.cursor/commands/<name>.md`（纯 Markdown、无 frontmatter） | 生成 `fengchao-<verb>.md` |
| OpenCode | `.opencode/commands/<name>.md`（frontmatter + `$ARGUMENTS`） | 生成 `fengchao-<verb>.md` |
| Codex | 仅全局 `~/.codex/prompts`（官方已标记 deprecated），无项目级约定 | 不生成薄命令，回退 AGENTS.md marker 块 |

### 与蓝图的实现偏差（3 处，均为落地时的合理化）

1. **B1 remind 模式输出**：蓝图未指定通道，实现为 stop-gate remind 打印到 stdout（Claude Code transcript 可见）、strict 走 `{"decision":"block"}` 协议；两种模式都在输出前落防重标记。
2. **附录 C `missing_task_record_for_changes`**：实现为仅当"当天既无 changelog 也无 task-record"时以 warning 附带提示（信息含"lite 交付可忽略"），changelog 存在时不再报——严格贯彻 B5"有 changelog 即可"。
3. **maintain 来源路径**：`--from-plan/--from-conversation` 同时接受记忆根相对与项目根相对路径（自动剥离记忆根前缀），dogfooding 中发现纯记忆根相对约定易用性差。

### 1.6 所列设计债的清偿情况

| 债 | 状态 |
|----|------|
| 真相层追加即腐化 | ✅ B4 语义合并替代 `update_domain_context()`，红线 9 生效，`doctor` 检出存量老式条目 |
| 侵入性过强（5 副本 + 6 顶层目录 + 整文件） | ✅ 新布局：`.fengchao/` + 记忆根，宿主全部 marker 块化 |
| 无停用/卸载/升级机制 | ✅ disable/enable/uninstall/upgrade，卸载对称性有逐字节测试 |
| 触发完全依赖 prompt 约定 | ✅ hooks 硬门禁（Claude Code）+ git pre-commit 兜底 + CI 提醒三层保险 |
| 路由子串匹配瓶颈 | ✅ 打分 v2（词级 + IDF + 时间衰减）+ 预算管制 |
| 模板三处并存失配 | ✅ 内联模板唯一事实源，`templates/`、`adapters/` 为生成产物，CI diff 校验 |
| 无版本概念、无发布渠道、无英文模板 | ✅ `__version__`/`installed_version`/`version_drift`、pyproject 打包、`--language en` 全套模板 |

---

## 附录 A：术语表

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
| 薄命令 | init 按 agent 生成的斜杠命令文件（route/remember/status 三动词），逻辑在 CLI 引擎 |
| marker 块 | `<!-- FENGCHAO-BUSINESS-MEMORY:START/END -->` 包裹的注入内容，保证可干净摘除 |
| 硬门禁 | 通过 hooks / check 强制记忆维护发生的机制，区别于 prompt 软约定 |
| 规则条目 | business-context 中一条结构化的现行业务规则（附录 B 格式），以规则名为稳定 key |
| 稳定 key | 规则条目的规则名：一经确立不随内容变化，是 delta 合并的定位锚点 |
| delta 合并 | maintain 以 added/modified/removed 语义写入真相层，替换/移除而非堆积（B4） |
| 轻档/重档（lite/full） | maintain 的两档仪式：无业务变化只记 changelog；有业务变化走完整链路（B5） |
| 诊断信封 | CLI 机器可读输出的统一结构 `{severity, code, message, target?, fix?}`（附录 C） |
| dogfooding | 本仓库用 FengChao 记录自身开发，既是测试也是活示例 |

## 附录 B：business-context 规则条目格式规范

> 本格式仅适用于 domain 文件"## 当前业务规则"段下的规则条目。术语、偏好、坑点、否定记忆不适用（见 B4 配套改动）。

**条目模板**：

```markdown
### 规则：设计单审核流程
- **规则**：设计单最终通过必须依次经过主管审核和经理审核。
- **场景**：设计师提交设计单后，主管一审通过、经理二审通过，设计单才进入"已通过"状态；任一级驳回则整单退回待修改。
- **来源**：[2026-07-07_001_设计单两级审核.md](../../task-records/2026-07-07_001_设计单两级审核.md)
- **生效**：2026-07-07
- **沿革**：[2026-05-12_002_设计单单级审核.md](../../task-records/2026-05-12_002_设计单单级审核.md)
```

**字段规则**：

| 字段 | 必填 | 规则 |
|------|------|------|
| 规则名（标题） | 是 | 稳定 key。业务对象 + 主题的名词短语（"设计单审核流程"）；不含日期、动词、实现词（类名/表名/文件名）；一经确立不改——内容变化走 modified 替换正文，key 不变 |
| 规则 | 是 | 单句、单一可观察业务事实。一个条目只说一件事，两件事拆两个条目 |
| 场景 | 强烈建议 | 一个具体例子（可用 GIVEN/WHEN/THEN 或自然语句）。自检问题："一个没看过代码的人，能否据此判断系统行为是否符合规则？" |
| 来源 | 是 | 指向确立当前内容的 task-record 相对链接（check 校验其存在） |
| 生效 | 是 | 当前内容的落地日期 |
| 沿革 | modified 后自动生成 | 历任旧版本的 task-record 链接，最近的在前；只保链接不保旧文本 |

**废除段格式**（domain 文件"## 已废除规则"段）：

```markdown
## 已废除规则

- ~~设计单加急通道~~：2026-07-07 由 [2026-07-07_002_取消加急通道.md](../../task-records/2026-07-07_002_取消加急通道.md) 废除
```

## 附录 C：诊断信封与退出码契约

**JSON 输出结构**（`--format json`，stdout 恰好一份 JSON 文档）：

```json
{
  "status": "ok | warn | error",
  "command": "check",
  "diagnostics": [
    {
      "severity": "error | warning | info",
      "code": "broken_link",
      "message": "Broken link in fengchao/task-records/TASK-INDEX.md: ...",
      "target": "fengchao/task-records/TASK-INDEX.md",
      "fix": "确认目标文件是否被误删或改名；修正索引中的链接后重跑 check"
    }
  ]
}
```

规则：可选键（`target`、`fix`）缺省时省略而非置 `null`；人读模式输出不变，JSON 模式下所有信息只走这份文档。

**退出码契约**：

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 / 校验通过 /（`--warn` 模式下恒为 0） |
| 1 | 校验失败 / 合并失败 / 运行时错误 |
| 2 | 参数或用法错误（argparse 缺省行为，保留） |
| 130 | 用户取消（Ctrl-C 或确认环节拒绝） |

**诊断 code 登记表**（新增诊断必须先在此登记）：

| code | severity | 来源 | 含义 |
|------|----------|------|------|
| `missing_required_file` | error | check | 必需脚手架文件缺失 |
| `broken_link` | error | check | Markdown 链接指向不存在的文件 |
| `missing_task_record_for_changes` | error/warning | check --strict / --warn | 有项目 git 变更但当天无 task-record（lite 交付按 B5 放宽为查 changelog） |
| `missing_changelog_for_changes` | error/warning | 同上 | 有项目 git 变更但当天无 changelog |
| `rule_already_exists` | error | maintain (B4 added) | 规则名已存在，应用 modified 或换名 |
| `rule_not_found` | error | maintain (B4 modified/removed) | 规则名不存在，附最相近候选清单 |
| `memory_map_row_too_long` | warning | check | memory-map 行超过长度上限（C1） |
| `orphan_record` | warning | doctor | 记录文件不在任何索引中 |
| `index_dead_row` | warning | doctor | 索引行指向已归档/移动的记录且未更新 |
| `legacy_layout` | info | status/doctor | 检测到老布局，建议 migrate |
| `legacy_context_entry` | info | doctor | 检测到老式追加条目，建议人工整理为规则条目 |
| `version_drift` | info | status/doctor | 项目内 skill 副本版本落后于 CLI 版本 |
