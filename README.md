# FengChaoSkills 蜂巢

[![CI](https://github.com/HappyLeoYang/FengChaoSkills/actions/workflows/ci.yml/badge.svg)](https://github.com/HappyLeoYang/FengChaoSkills/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/fengchao-skills)](https://pypi.org/project/fengchao-skills/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://github.com/HappyLeoYang/FengChaoSkills/blob/master/pyproject.toml)

**给 AI 编程会话装一个"项目业务记忆"。** 你和 AI 聊出来的业务知识——为什么这么设计、某个词指什么、哪个方案被否掉了——不再随会话关闭而丢失，而是沉淀成项目里的一套 Markdown 文档，下次开新会话时 AI 自动找回来接着用。

> FengChao is an agent-agnostic business-memory toolkit for AI coding sessions, built on plain Markdown + Git. Zero dependencies, zero telemetry.

支持 Claude Code / Cursor / OpenCode / Codex 及一切读 `AGENTS.md` 的工具。零第三方依赖 · 零遥测 · 零网络请求 · 记忆数据永远属于你。

## 它解决什么问题

AI 编程会话是无状态的。代码在 git 里，但**业务语义**只存在于对话里：

- 你上周花半小时给 AI 解释过"审核为什么分两级"，今天开新会话，又得解释一遍；
- AI 把"讨论过"当成"已实现"，把"随口一提"当成"业务规则"；
- 你上个月明确否定过的方案，AI 这个月又原样提了一遍。

FengChao 干的事很简单：**每次真实交付后，把业务事实和证据记下来；每次新会话开始，把最相关的那几条找回来。** 并且严格区分"当前事实"和"历史参考"——被否掉的方案会被记住是"被否掉的"，不会复活。

它和 OpenSpec / Spec Kit 这类 Spec 工具不冲突：Spec 管"接下来做什么"（事前），FengChao 管"业务认知为什么是现在这样"（事后），可以共存。

## 安装

在你的项目根目录执行一条命令：

```bash
cd your-project

# 方式一（推荐）：免安装直接运行
uvx fengchao-skills init          # 或 pipx run fengchao-skills init

# 方式二：git clone 后直接跑，零前置依赖（只需 Python 3.9+）
git clone https://github.com/HappyLeoYang/FengChaoSkills.git ~/FengChaoSkills
python3 ~/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py init
```

`init` 会交互式询问你在用哪个 AI 工具（也可直接 `--agents claude,cursor`，会自动探测已有的 `.claude/`、`.cursor/` 目录）。装完验证：

```bash
uvx fengchao-skills status        # 全绿即安装成功
```

## 装完后你的项目长什么样

所有写入都可见、可 diff、可干净移除：

```
your-project/
├── .fengchao/                  # 工具安装点：配置 + skill 副本（可整体删除）
├── fengchao/                   # 你的业务记忆，纯 Markdown（属于你，建议提交进 git）
│   ├── FENGWANG.md             #   路由入口：AI 新会话从这里找记忆
│   ├── memory-map.md           #   记忆总索引
│   ├── business-context/       #   当前业务真相（每条规则只有一个现行版本，带证据）
│   ├── task-records/           #   每次交付的任务记录：意图、方案、证据
│   ├── changelog/              #   已落地的变更历史
│   ├── plan-records/           #   计划记录（proposed → implemented 状态流转）
│   └── conversation-records/   #   你的业务解释、术语、偏好、否定过的方案
├── .claude/ .cursor/ ...       # 各 AI 工具的薄入口（每个文件 ≤ 10 行）
└── CLAUDE.md / AGENTS.md       # 追加一个 ≤ 15 行的 marker 块，原内容一字不动
```

隐私默认：只保存萃取后的摘要，永不保存完整对话。

## 怎么使用

**日常你什么都不用做，正常开发即可**：

- 开新会话时，AI 自动从 `fengchao/FENGWANG.md` 路由回相关业务记忆；
- 真实交付后，AI 自动沉淀任务记录 + changelog（会话结束时有门禁提醒，remind / strict / off 三档可调）；
- 纯修复、重构只记一条 changelog，不制造记忆噪音。

想主动用，一共三个动词（在 Claude Code 中是斜杠命令，其他工具类似）：

| 命令 | 干什么 |
|------|--------|
| `/fengchao:route <关键词>` | 找回相关的业务记忆 |
| `/fengchao:remember` | 把刚才聊的业务解释记进去 |
| `/fengchao:status` | 看看记忆系统当前状态 |

一条重要原则：**只有你用肯定语气断言的事实才会进"业务真相"层**。疑问句、"我记得好像"、AI 自己读代码猜出来的结论，都不算数——宁可漏记，不可误记。

## 怎么更新

```bash
cd your-project
uvx fengchao-skills upgrade       # uvx 自动拉最新版；upgrade 只刷新工具本体
```

源码方式：先 `git pull` 更新克隆的仓库，再运行同一条 `upgrade`。

`upgrade` 只重写 `.fengchao/` 里的工具文件和宿主注入，**绝不触碰 `fengchao/` 记忆数据**。

## 怎么停用 / 卸载

三级分离，随时反悔：

```bash
uvx fengchao-skills disable                    # 暂停：摘除全部注入，enable 逐字节还原
uvx fengchao-skills uninstall                  # 卸载工具：删 .fengchao/，记忆文档保留
uvx fengchao-skills uninstall --purge-memory   # 连记忆一起删（需二次确认）
```

`disable` 之后 `git diff` 干净可读。即使彻底卸载，`fengchao/` 仍是一套完好的、人类可读的 Markdown 文档库——记忆数据永远属于你。

## 支持的 AI 工具

| 工具 | 接入方式 |
|------|----------|
| Claude Code | 薄入口 + 斜杠命令 + hooks 自动门禁 |
| Cursor | rule + 命令 |
| OpenCode | 命令 + opencode.json |
| Codex / 其他读 `AGENTS.md` 的工具（Pi、Kimi Code、智谱 ZCode 等） | `AGENTS.md` marker 块，开箱即用 |

不用以上任何工具也能用：`fengchao-skills install-git-hook` 提供可选的 git pre-commit 钩子兜底。

## 文档

- [快速上手](docs/getting-started.md) · [核心概念](docs/concepts.md) · [术语表](docs/glossary.md)
- [团队协作](docs/team-workflow.md) · [在已有大项目中引入](docs/existing-projects.md)
- [FAQ](docs/faq.md) · [故障排查](docs/troubleshooting.md) · [CI 集成](docs/ci.md)
- [总体设计蓝图](docs/DESIGN.md) · [演示样例](examples/README.md)

## 信任声明

- **零第三方依赖**：核心只用 Python 标准库，你的项目不需要安装任何东西。
- **零遥测、零网络请求**：没有任何数据离开你的机器。
- **记忆数据神圣**：任何命令都不会在无显式确认下删除或改写记忆内容。
- **token 开销可量化**：每会话固定注入约 ≤ 260 tokens，路由输出有 4KB 硬预算，实测数据见 [FAQ](docs/faq.md#会多消耗多少-tokens实测数据)。

## License

MIT
