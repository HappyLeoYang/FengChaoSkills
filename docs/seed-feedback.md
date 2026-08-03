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
| F-005 | 2026-07-28 | 种子用户（维护者转述） | hook 路径缺陷 | **Stop（stop-gate）hook 用相对路径，工作目录在子目录时找不到脚本而报错**。两层根因：① hook 命令写死相对路径 `python3 .fengchao/skill/scripts/fengchao.py hook stop-gate`（`CLI_RELATIVE` 常量 `fengchao.py:39`，拼装于 `:961`）；Claude Code hook 以会话当前工作目录为 cwd，当 cwd 在子目录（如 `spikes/spike2_engine/`）时相对路径解析到子目录、找不到脚本 → 报错。② 即便修好脚本路径，`hook_project` 仍用 `os.getcwd()` 当项目根（`fengchao.py:3403` + `:2650` 查 `.fengchao/config.yaml`），在子目录里查不到 config 会**静默空跑**（`return EXIT_OK`），记忆维护门禁无声失效。同一相对路径还出现在 session-start 注入的 maintain 提示命令（`:2663`）与 `maintain_skeleton`（`:2639`），子目录下 AI 照抄也会失败。 | 已修复（v0.2.1：hook 命令改 `python3 "${CLAUDE_PROJECT_DIR:-.}/.fengchao/skill/scripts/fengchao.py" hook ...`；hook 子命令 env→walk-up→cwd 解析项目根；session-start 注入与 maintain 骨架改带引号绝对路径；LEGACY 前缀清单保证旧格式条目升级替换、卸载对称摘除。存量项目需在项目根跑一次 `upgrade` 刷新 settings.json，见 troubleshooting） | [task 2026-08-02_001](../fengchao/task-records/2026-08-02_001_v0.2.1：hook-任意-cwd-生效（f-005）.md) |

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
