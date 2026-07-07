# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

FengChaoSkills 是一个多 Agent 业务记忆工具包（本仓库是源码/分发仓库，不是被安装的目标项目）。它通过 `fengchao.py init` 把整个 skill 目录复制安装到目标项目中，帮助 AI 会话路由项目记忆、保存业务意图和开发证据。

## 常用命令

无构建、无 lint、零第三方依赖（`fengchao.py` 刻意只用 Python 标准库，保证目标项目无需安装任何依赖——修改时必须维持这一约束）。

```bash
# 运行全部测试（在仓库根目录）
python3 -m unittest discover -s tests -v

# 运行单个测试
python3 -m unittest tests.test_fengchao_cli.FengChaoCliTests.test_init_creates_project_memory_artifacts_and_adapters

# 手动验证 CLI（在临时目录中执行，避免污染本仓库）
python3 skills/fengchao-business-memory/scripts/fengchao.py --help
```

测试通过 `subprocess` 在临时目录中调用真实 CLI，属于端到端测试，不 mock。

## 核心架构

### 唯一逻辑入口：`fengchao.py`

所有逻辑集中在 `skills/fengchao-business-memory/scripts/fengchao.py`（单文件 CLI）。同目录的 `check_links.py`、`inspect_project.py`、`check_required_updates.py`、`next_record_name.py` 只是兼容性薄包装，直接 import 并调用 `fengchao.py`。

CLI 子命令与记忆写入的对应关系（这是本项目的核心业务规则）：

| 子命令 | 写入目录 | 语义 |
|--------|----------|------|
| `init` | 全部脚手架 | 在目标项目初始化记忆目录和各 Agent 规则文件 |
| `fengwang --query` | 只读 | 按 `fengwang/memory-map.md` 打分路由到相关记忆文件 |
| `plan` | `plan-records/` + memory-map | 记录最终计划，**不是**当前业务事实 |
| `conversation` | `conversation-records/` + memory-map | 记录用户业务解释，**不是**当前业务事实 |
| `maintain` | `task-records/` + `changelog/` + memory-map，有 `--business-change` 时才写 `business-context/` | 仅真实开发交付后使用 |
| `check` | 只读 | 校验必需文件存在 + Markdown 链接完整性；`--require-records-for-git-changes` 额外要求有 git 变更时当天必须有 task/changelog 记录 |

CLI 以 **当前工作目录** 作为目标项目根，配置读取 `.fengchao/config.yaml`（手写逐行解析，非 YAML 库，只支持扁平 `key: "value"` 格式）。

### 记忆分层语义（六个目录）

- `business-context/`：当前业务真相，只有已落地的稳定事实才能进入。
- `task-records/`、`changelog/`：已交付任务的不可变证据，仅开发完成后写入。
- `plan-records/`、`conversation-records/`：历史/参考记忆，默认不提升为当前真相。
- `fengwang/`：路由入口（`FENGWANG.md` + `memory-map.md`），所有写入命令都会追加 memory-map 行。

记录文件命名规则：`YYYY-MM-DD_NNN_标题slug.md`，NNN 为当天序号（见 `next_record_path`）。

### 关键陷阱：模板内容三处并存

生成到目标项目的文件内容以 `fengchao.py` 内的 Python 字符串函数为准（`context_index_template`、`fengwang_template`、`agents_snippet`、`claude_snippet`、`cursor_rule`、`opencode_config` 等）。仓库中的 `templates/` 和 `adapters/` 目录是给人看的参考副本，**不被 CLI 读取**，且内容与内联模板并不完全一致（如 adapter snippet 为英文、内联生成为中文）。修改生成产物必须改 `fengchao.py`，并手动同步 `templates/`、`adapters/` 与 `README.md` 中的对应内容。

### Skill 分发结构

`skills/fengchao-business-memory/` 是完整的可分发单元：`SKILL.md`（Agent 入口）+ `references/`（各模式的详细规则）+ `scripts/`。`init` 会把该目录整体复制到目标项目的 `.opencode/.claude/.cursor/.codex/.agents` 五个 `skills/fengchao-business-memory/` 路径下（清单见 `PROJECT_SKILL_PATHS`），新增文件时注意会被一并分发。

## 内容语言约定

生成的记忆产物默认中文（`language: zh-CN`）；代码标识符用英文，测试断言大量依赖中文模板文案，改动模板措辞会连带影响测试。
