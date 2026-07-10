# FengChaoSkills 蜂巢

[![CI](https://github.com/HappyLeoYang/FengChaoSkills/actions/workflows/ci.yml/badge.svg)](https://github.com/HappyLeoYang/FengChaoSkills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://github.com/HappyLeoYang/FengChaoSkills/blob/master/pyproject.toml)

> Agent 无关的**项目业务事实账本**：让 AI 会话在真实开发交付后自动沉淀"业务真相 + 落地证据"，在新会话开始时按最小必要集合路由回这些记忆，并严格区分"当前事实"与"历史参考"。
>
> FengChao is an agent-agnostic, Markdown + Git based **business fact ledger** for AI coding sessions: it captures business truth with evidence after real delivery, routes the minimal memory set into fresh sessions, and never confuses "current fact" with "historical reference".

零第三方依赖 · 零遥测 · 零网络请求 · 纯 Markdown + Git · 记忆数据永远属于你

## 它解决什么问题

AI 编程会话是无状态的。代码在 git 里，但**业务语义**只存在于对话中：为什么审核要分两级？"主管"指什么岗位？用户上个月否定过哪个方案？会话关闭，知识就死了。更危险的是记忆污染：把"讨论过"当"已实现"、把"随口一提"当"业务规则"、把"已废弃"当"当前行为"。

FengChao 用两个别人基本没做的设计解决这两个问题：

1. **记忆的认识论分层**：五级可信度 + 冲突优先级（`business-context` 当前真相 > `task-records/changelog` 落地证据 > implemented plan > `conversation-records` > proposed plan）。
2. **否定记忆**：用户明确拒绝过的方案会被记录，防止 AI 把被否掉的方案再提一遍。

与 Spec 工具（OpenSpec / Spec Kit）不冲突：它们管"接下来做什么"（事前），FengChao 管"业务认知为什么是现在这样"（事后），可共存。

## 60 秒 Quick Start

```bash
cd your-project

# 方式一（推荐，发布后可用）：免安装一次性运行
uvx fengchao-skills init     # 或 pipx run fengchao-skills init

# 方式二（当前可用）：git clone 后直接跑，零依赖
git clone https://github.com/HappyLeoYang/FengChaoSkills.git ~/FengChaoSkills
python3 ~/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py init
```

`init` 交互选择 agent（或 `--agents claude,cursor`，会自动探测已有的 `.claude/`、`.cursor/` 等目录），然后立刻验证：

```bash
uvx fengchao-skills status    # 全绿即可（源码方式则用 python3 .../fengchao.py status）
```

### init 写入了什么（全部可见、可 diff、可干净移除）

| 写入 | 内容 |
|------|------|
| `.fengchao/` | 唯一工具安装点：config.yaml + skill 完整副本（可整体删除） |
| `fengchao/` | 唯一记忆根：FENGWANG.md 路由入口 + 六层记忆目录（**属于你**，建议入 git） |
| `.claude/` `.cursor/` 等 | 薄入口 + 三个斜杠命令（每个文件 ≤ 10 行，只指向 `.fengchao/skill/`） |
| `CLAUDE.md` / `AGENTS.md` | 一个 marker 块（≤ 15 行，`disable` 精确摘除，原内容一字不动） |
| `.claude/settings.json` | SessionStart / Stop 两个 hook（可 `--no-hooks` 关闭） |

## 日常使用：你什么都不用做

正常开发即可。路由和维护由 skill 规则 + hooks 驱动：

- 新会话自动从 `fengchao/FENGWANG.md` 路由回业务记忆（SessionStart hook）；
- 真实开发交付后自动沉淀 task-record + changelog（Stop hook 门禁：remind / strict / off 三档）；
- 纯修复/重构走 lite 档只记一条 changelog，不制造记忆噪音。

想主动用，三个动词（Claude Code 中为 `/fengchao:route` 等）：

| 命令 | 作用 |
|------|------|
| `/fengchao:route <关键词>` | 找回相关业务记忆 |
| `/fengchao:remember` | 把刚才的业务解释记入记忆 |
| `/fengchao:status` | 看看记忆系统状态 |

## 停用与卸载（三级分离，随时反悔）

```bash
uvx fengchao-skills disable     # 暂停：摘除全部注入，记忆和工具本体全保留；enable 逐字节还原
uvx fengchao-skills uninstall   # 移除工具：删 .fengchao/，记忆文档保留（它属于你）
uvx fengchao-skills uninstall --purge-memory   # 连记忆一起删，需要二次确认
```

`disable` 后 `git diff` 干净可读；每一个写入你项目的字节都有对应的干净摘除路径。即使卸载，记忆仍是一套完好的、人类可读的 Markdown 文档库。

## 六层记忆模型

| 目录 | 语义 | 写入时机 |
|------|------|----------|
| `business-context/` | 当前业务真相（每条规则一个现行条目，带证据链） | 仅稳定业务事实落地后，经语义合并写入 |
| `task-records/` | 已交付任务的业务意图、方案、证据（不可变） | 仅真实开发交付后（full 档） |
| `changelog/` | 已落地变更历史（不可变） | 任何真实交付（lite/full 档） |
| `plan-records/` | 最终计划（proposed → implemented 状态流转） | Plan 产出最终计划后 |
| `conversation-records/` | 用户业务解释、术语、偏好、**否定项** | 用户给出长期有价值的解释后 |
| `FENGWANG.md` + `memory-map.md` | 路由入口 | 所有写入命令自动追加 |

隐私默认：只保存萃取摘要，永不保存完整对话。

## 支持的 Agent Surface

Claude Code（薄入口 + 斜杠命令 + hooks 硬门禁）· Cursor（rule + 命令）· OpenCode（命令 + opencode.json）· Codex / 通用 Agents（AGENTS.md marker 块）。不用 Claude Code 也能用：五个 surface + 可选 git pre-commit 钩子兜底（`fengchao-skills install-git-hook`）。

## 文档

- [快速上手](docs/getting-started.md) · [核心概念](docs/concepts.md) · [术语表](docs/glossary.md)
- [团队协作](docs/team-workflow.md) · [在已有大项目中引入](docs/existing-projects.md)
- [FAQ](docs/faq.md) · [故障排查](docs/troubleshooting.md) · [CI 集成](docs/ci.md)
- [总体设计蓝图](docs/DESIGN.md) · [开源发布路线图](docs/release-plan.md) · [演示样例](examples/README.md)

## 信任声明

- **运行时零第三方依赖**：`fengchao.py` 只用 Python 标准库，目标项目无需安装任何东西。
- **零遥测、零网络请求**：没有任何数据离开你的机器。
- **记忆数据神圣**：任何命令（uninstall/upgrade/migrate/compact）都不会在无显式确认下删除或改写记忆内容。

## License

MIT
