# 种子用户反馈表（Phase R3）

> 性质：R3 种子用户测试阶段的反馈登记与处置台账。维护者在对话中转述的每条反馈都登记于此；处置结论回填后，修复走 release-plan.md 第四节 SOP 发 patch 版本，产品级调整记入 DESIGN.md 修订。
> 编号规则：`F-` + 三位递增序号，一经分配不复用。
> 重点收集维度见 [release-plan.md](release-plan.md) Phase R3：安装体验 / 打扰度 / maintain 记录质量 / 路由价值 / 停用体验。

## 反馈台账

| 编号 | 日期 | 来源 | 维度 | 反馈内容 | 处置状态 | 落地链接 |
|------|------|------|------|----------|----------|----------|
| F-001 | 2026-07-12 | 维护者本人实测（macOS，有 Python 无 uv/pipx） | 安装体验 | README 方式一 `uvx fengchao-skills init` 直接 `command not found`，`pipx run` 同样；只有 Python 环境的普通用户照抄 Quick Start 第一行即撞墙，且文档未说明 uvx/pipx 需要前置安装 | 已落地（v0.2.1，维护者拍板方案②：uvx 主推 + 前置一行标注，README 与 getting-started 同步） | [task 2026-08-02_002](../fengchao/task-records/2026-08-02_002_v0.2.1：migrate-链接改写边界修复（f-003）+-安装文档与-token-实测.md) |
| F-002 | 2026-07-12 | 种子用户（维护者转述） | token 成本 | 引入本 skill 相比不使用会多消耗多少 tokens？有没有量化预估？成本构成：宿主 marker 块与薄入口的常驻注入、SessionStart 路由注入（FENGWANG + `fengwang --query` 输出，≤4KB 预算）、路由命中后被读取的记录文件（8–12 个最小集合）、maintain/自检的额外输出、stop-gate 提醒文本 | 已复盘（v0.2.1 实测：每会话固定注入 ≤260 tokens、路由 4KB 硬预算、交付提醒 ≤165 tokens；结论与对照分析见 [faq.md](faq.md#会多消耗多少-tokens实测数据) 与 README 信任声明第 4 条） | [task 2026-08-02_002](../fengchao/task-records/2026-08-02_002_v0.2.1：migrate-链接改写边界修复（f-003）+-安装文档与-token-实测.md) |
| F-003 | 2026-07-20 | 维护者迁移真实老项目（ShenNongYuAi）时发现 | migrate 缺陷 | **`migrate` 过度剥离 `../` 导致外部链接断裂**：链接改写假设所有 `../` 都指向同级记忆目录，无脑执行 `](../ → ](`。但 memory-map 常引用记忆根之外的项目文件（如 `../docs/业务文档.md`、`../ui/设计稿.jsx`）。由于新记忆根 `fengchao/` 与旧 `fengwang/` 同深度，这些外部链接的 `../` 本应保留，被误删后指向不存在的 `fengchao/docs/...`，`migrate` 收尾 check 直接报 7 个 `broken_link`。当前只能人工还原 `../`。 | 已修复（v0.2.1：改写换边界锚定 regex，只剥指向五个记忆目录的 `../`，外部链接原样保留；覆盖 markdown 链接与反引号裸路径两种形态；migrate 测试新增外部链接回归场景。经推演 archive 的前缀追加语义对内外链接均保真、不属同类 bug，已加注释防误报） | [task 2026-08-02_002](../fengchao/task-records/2026-08-02_002_v0.2.1：migrate-链接改写边界修复（f-003）+-安装文档与-token-实测.md) |
| F-004 | 2026-07-23 | 维护者提出（评估新增 agent 支持） | agent surface 扩展 | 是否需要为 **Pi / Kimi Code / 智谱 ZCode / MiniMax code** 四个工具新增独立 surface？调研结论见下方「F-004 调研详录」。**判断：四个都不需要独立 surface**——`AGENTS.md` 已成事实标准，现有 `agents` surface 输出的根 `AGENTS.md` marker 块今天就覆盖 Pi/Kimi/ZCode；MiniMax code 是 M2 模型跑在宿主 harness 里（Claude Code/Cursor 等已覆盖），无独立编码 harness。 | 已落地（v0.2.1：README「支持的 Agent Surface」注明任何读 `AGENTS.md` 的工具开箱即用；判断维持"无需独立 surface"，可选增强清单保留在下方详录中待未来评估） | [task 2026-08-02_002](../fengchao/task-records/2026-08-02_002_v0.2.1：migrate-链接改写边界修复（f-003）+-安装文档与-token-实测.md) |
| F-006 | 2026-08-10 | 种子用户（维护者转述） | maintain 链接缺陷 | **`maintain --from-conversation` 传裸记录名时生成断链**：产出 `../<名字>`，缺 `conversation-records/` 目录段与 `.md` 后缀，`check` 当场报 `broken_link`，用户只能手工改路径。根因：`project_relative_link_list()`（`fengchao.py:1462`）对入参仅做"无 `../` 前缀则补 `../`"，不补目录段也不补后缀；上游 `normalize_memory_relative()`（`:1451`）只剥记忆根前缀，同样无补全。即隐含契约要求调用方传记忆根相对完整路径（`conversation-records/xxx.md`，实测该格式正常），但 SKILL.md/references 未记载此契约，AI 或用户传裸名即踩坑。**`--from-plan` 同一代码路径，同样受影响**。已在临时目录端到端复现（裸名断链、完整路径通过）。 | 已修复（v0.2.2：`normalize_memory_relative()` 增 `default_dir` 参数，剥记忆根前缀后补默认目录段（值内无 `/` 时）与 `.md` 后缀，`--from-plan`/`--from-conversation` 分别传 `config.plan_dir`/`config.conversation_dir`；裸名/记忆根相对/项目根相对三种写法归一，`../` 外部引用原样保留（沿用 F-003 边界纪律）；传参契约补进 SKILL.md 与 task-record-system.md，新增 SourceLinkTests 三写法回归） | [task 2026-08-10_001](../fengchao/task-records/2026-08-10_001_v0.2.2：maintain-来源链接补全（f-006）.md) |
| F-005 | 2026-07-28 | 种子用户（维护者转述） | hook 路径缺陷 | **Stop（stop-gate）hook 用相对路径，工作目录在子目录时找不到脚本而报错**。两层根因：① hook 命令写死相对路径 `python3 .fengchao/skill/scripts/fengchao.py hook stop-gate`（`CLI_RELATIVE` 常量 `fengchao.py:39`，拼装于 `:961`）；Claude Code hook 以会话当前工作目录为 cwd，当 cwd 在子目录（如 `spikes/spike2_engine/`）时相对路径解析到子目录、找不到脚本 → 报错。② 即便修好脚本路径，`hook_project` 仍用 `os.getcwd()` 当项目根（`fengchao.py:3403` + `:2650` 查 `.fengchao/config.yaml`），在子目录里查不到 config 会**静默空跑**（`return EXIT_OK`），记忆维护门禁无声失效。同一相对路径还出现在 session-start 注入的 maintain 提示命令（`:2663`）与 `maintain_skeleton`（`:2639`），子目录下 AI 照抄也会失败。 | 已修复（v0.2.1：hook 命令改 `python3 "${CLAUDE_PROJECT_DIR:-.}/.fengchao/skill/scripts/fengchao.py" hook ...`；hook 子命令 env→walk-up→cwd 解析项目根；session-start 注入与 maintain 骨架改带引号绝对路径；LEGACY 前缀清单保证旧格式条目升级替换、卸载对称摘除。存量项目需在项目根跑一次 `upgrade` 刷新 settings.json，见 troubleshooting） | [task 2026-08-02_001](../fengchao/task-records/2026-08-02_001_v0.2.1：hook-任意-cwd-生效（f-005）.md) |
| F-007 | 2026-08-23 | 维护者提出（能力缺口讨论） | 萃取能力缺口 | **缺「对话中自动提炼项目事实」的能力**：现有五个模式全是被动记录（用户讲了才记 / 交付完了才记），缺的是在对话过程中从**用户确凿语气的断言式表述**中主动识别并登记项目事实。事实类型是多样的——业务规则、系统入口、关键词、术语、确凿的配置值、固定的代码信息（常量/约定），不限于任何单一形态（**明确不是要记接口文档**）。落地形态要求渐进式披露：索引薄、细节按需展开。当前障碍见下方「F-007 现状盘点」：① `extraction-quality.md` 五问自检全在业务侧，没有一问触发"把事实锚定到项目具体位置"；② `conversation` 的六个固定字段（背景/术语/偏好/否定/未验证/关联）容不下配置值、入口、代码常量这类事实，只能硬塞进"术语"或"背景"；③ `context-system.md` 规约里写了 domain 文件应含 entry points，但该段不受 `merge_domain_rule()` 管辖、无任何写入通道，是一段死规约；④ 触发条件"用户在解释业务背景"过窄且主观，缺可判定的确凿性信号清单。 | 已落地（v0.3.0：新增第六种记忆模式「事实登记」与受管文件 `business-context/project-facts.md`；`conversation --confirmed-fact "名称=值" / --fact-kind / --retire-fact` 打通"用户明确确认"这条**规约早已允许、CLI 却无通道**的晋升路径；事实名为稳定 key，同名覆盖并把旧来源转入沿革，未显式给类别时沿用旧类别；先验证后写入——入参非法或废除不存在的事实时整体失败，连对话记录都不留；memory-map 行幂等 upsert，受管文件反复写入不长出重复行；护城河在 `extraction-quality.md` 第五节「确凿性信号清单」，从严起步；红线 9 扩展覆盖事实名，新增红线 10「确凿性门槛」） | [task 2026-08-23_001](../fengchao/task-records/2026-08-23_001_v0.3.0：确凿事实登记（f-007）.md) |

## F-007 现状盘点与方案讨论（2026-08-23）

### 一、现状能力盘点（代码级核实）

| 环节 | 现状 | 结论 |
|------|------|------|
| 术语登记 | `conversation --term` 自由文本 append（`fengchao.py:1752` 模板「业务术语与含义」段） | 能写，但无结构、写不写全凭 AI 自觉 |
| 入口登记 | `context-system.md` 要求 domain 文件含 `Core entry points`，但受管段只有「当前业务规则」「已废除规则」两段 | **死规约**：无写入通道，`maintain` 不会碰它 |
| 配置/代码常量登记 | 无对应字段 | 缺失，只能塞进 summary |
| 路由命中 | `collect_keywords()` 抽 `[\w一-鿿]+`、`tokenize_for_scoring()` 走 `[a-z0-9_]+` + 中文 2-gram + IDF | **技术上通**：罕见标识符（接口名/常量名）IDF 权重高，写进去就能被命中；缺的是"保证写进去" |
| 触发时机 | 五模式均为被动（plan/conversation/maintain 由用户动作触发） | 缺主动识别 |

### 二、必须先定的红线争议

事实来源不同，可信度不同，不能一视同仁地进真相层：

- **用户断言**（"设计单提交审核就是走这个接口"）→ 用户是业务权威，可视为确凿；
- **AI 从代码反推**（读 service 链路推出"提交时校验 BOM 非空"）→ 只是**代码事实**，不等于业务意图（可能是历史遗留、防御性代码，甚至是 bug）。

撞红线 7（未落地/未确认不进真相层）与 SKILL.md "git diff is supporting evidence, not the source of business meaning"。**倾向结论**：代码反推的结论只能落 `conversation-record` 的「仍未验证」段或 `--promote candidate`，须经用户确认才升入 domain 真相层；否则本 skill 会从"业务记忆"退化为"AI 猜的代码摘要"。

### 三、方案分层与拍板结果

| 层 | 内容 | 结果 |
|----|------|------|
| **A** | 补**确凿性信号清单**（何种表述算断言、何种算讨论中的倾向），让触发条件可判定 | ✅ 已落地为 `extraction-quality.md` 第五节，含"同一句话里的成分分开判定"对照表 |
| **B** | 事实的结构化写入通道与路由加权 | ✅ 已落地：**不加封闭字段枚举**（入口/配置/常量是开放集合，硬编码必漏），改为统一 `--confirmed-fact "名称=值"` + 自由文本 `--fact-kind` 标签；事实名与值优先入 keywords，`TYPE_BONUS` 给 `fact` 1.5 加权 |
| **C** | 反向萃取工作流（给入口 → 读链路 → 产出**候选**事实） | ✅ 按红线争议结论落为纪律而非新子命令：AI 读码结论强制走"未验证/candidate + 用户确认"，写进红线 10 与 `memory-promotion-rules.md` |

**用户拍板的关键取舍**：确凿性清单**从严起步**（宁可漏记，不可误记）——清单过宽会每轮对话都产出记录，稀释真正的事实并抬高 token 成本。

### 三之二、实施中修正的两处设计判断

1. **原计划"到 stop-gate 批量提示"不成立**：stop-gate 仅在**有 git 变更且当天无 changelog** 时触发（`hook_project`），而"用户在对话中断言事实"的典型场景是**纯讨论会话、零 git 变更**，根本不会触发。若为此新增触发条件，则每次会话都提示，违反 B1 防打扰设计。**改为**：AI 在当前回复末尾附一行确认（不另起一轮、不打断），用户点头后写入——零 hook 改动、零常驻成本。规约写在 `extraction-quality.md` 5.5。
2. **覆盖事实时类别会被静默洗掉**：一次命令共用一个 `--fact-kind`，覆盖旧事实时若本次未显式给类别，会把 `entry-point` 洗成默认 `general`。**改为**：未显式指定时从旧条目沿用原类别（`extract_field_value`）。类别不同的事实分两次命令登记。

### 四、已识别风险

1. **锚点会腐烂**：接口改名、常量重构后记忆变死链，而 `check` 无法校验（CLI 零依赖、跨语言，不解析目标项目源码）。文档须明写"锚点是线索，不是保证"。
2. **别长成 API 文档**：一旦开始记参数、字段、返回值，就退化为低质量 Swagger 副本。只记"业务名 ↔ 位置"这一层映射，往下不记。
3. **别长成噪音收集器**：确凿性信号清单如果过宽，每次对话都产出记录，会稀释真正的业务事实并抬高 token 成本（对照 F-002 的预算纪律）。

## F-004 调研详录（2026-07-23，四个编码工具的项目规则约定）

> 判断标准：一个工具是否需要 FengChao 独立 surface，取决于它是否读**独立于现有约定的**项目规则/记忆文件。读根 `AGENTS.md` 的 → 现有 `agents` surface 已覆盖；读 `CLAUDE.md`/`.claude/` 的 → `claude` surface 覆盖；只有用自有独立目录约定的才需要新增。

| 工具 | 项目规则约定 | 是否需独立 surface | 依据 |
|------|--------------|--------------------|------|
| **Pi**（earendil-works/pi，Mario Zechner） | 读根 `AGENTS.md`（启动注入 system prompt；发现路径：`~/.pi/agent/AGENTS.md` 全局 + 逐级父目录 + 当前目录，拼接）；另有 `APPEND_SYSTEM.md` 放全局行为规则 | ❌ 否，`agents` surface 覆盖 | 官方约定即 AGENTS.md |
| **Kimi Code**（MoonshotAI/kimi-cli） | 读 `AGENTS.md`（`/init` 生成；层级 `./AGENTS.local.md`、`./AGENTS.md` 或 `./.kimi/AGENTS.md`、`~/.kimi/AGENTS.md`、`/etc/kimi/AGENTS.md`）。**目前只认 AGENTS.md 不认 CLAUDE.md**（issue #2401 请求兼容） | ❌ 否，`agents` surface 覆盖 | 根 AGENTS.md 即生效 |
| **智谱 ZCode**（Z.ai，GLM-5.2） | 桌面级 ADE，每个任务开始读项目根 `AGENTS.md` 作为项目级指令记忆 | ❌ 否，`agents` surface 覆盖 | 官方推荐"先写 AGENTS.md" |
| **MiniMax code** | MiniMax **无独立编码 harness**：M2 是模型，通过 Anthropic 兼容端点跑在 Claude Code / Cursor / Cline / Kilo 等宿主里；MiniMax CLI(MMX) 是**媒体生成工具**（图/视频/语音），不读项目规则，输出到 `minimax-output/` | ❌ 否，由宿主 harness 覆盖 | M2 骑现有 harness；MMX 非规则读取型 |

**可选未来增强（非必需，基线已覆盖）：**
1. 为有独立命令目录的工具（Kimi skills、ZCode `/`命令）生成三动词薄命令——若用户想要主动动词入口；
2. hooks 硬门禁目前仅 Claude Code；Pi/Kimi/ZCode 走"规则驱动"档（同 Cursor/OpenCode），若某工具日后提供 hook 机制再做硬门禁对接；
3. Kimi 的 `.kimi/AGENTS.md` 备选发现路径——评估是否加薄入口（根 AGENTS.md 已够用，优先级低）；
4. 文档增强：README「支持的 Agent Surface」可注明"任何读 `AGENTS.md` 的工具（Pi/Kimi/ZCode 等）经通用 `agents` surface 开箱即用"，把 AGENTS.md 标准兼容性作为卖点。

**来源**：[MoonshotAI/kimi-cli #850](https://github.com/MoonshotAI/kimi-cli/issues/850) · [#2401](https://github.com/MoonshotAI/kimi-cli/issues/2401) · [earendil-works/pi](https://github.com/earendil-works/pi) · [pi.dev](https://pi.dev/) · [ZCode 指南](https://www.digitalapplied.com/blog/zcode-glm-5-2-agentic-development-environment-guide) · [MiniMax M2](https://github.com/MiniMax-AI/MiniMax-M2) · [MiniMax CLI 文档](https://platform.minimax.io/docs/token-plan/minimax-cli) · [awesome-cli-coding-agents](https://github.com/bradagi/awesome-cli-coding-agents)

## 处置原则（维护者拍板的产品判断，后续反馈处置须遵循）

1. **安装命令必须一条直达**（F-001 引出，2026-07-12）：用户不会愿意操作两次——先装 uv 再装本工具的两步流程不可接受为主推路径。候选方案：① Quick Start 把零前置依赖的路径提为方式一；② uvx 路径明确标注前置条件并附一条安装命令；③ 提供 curl 一键脚本。**已定（2026-08-02）：采用方案②**，v0.2.1 落地；方案③若 R3 后续仍有安装反馈再评估。
