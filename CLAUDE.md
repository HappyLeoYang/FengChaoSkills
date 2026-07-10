# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

FengChaoSkills 是一个多 Agent 业务记忆工具包（本仓库是源码/分发仓库，不是被安装的目标项目）。它通过 `fengchao.py init` 在目标项目安装单一工具点（`.fengchao/`）与单一记忆根（默认 `fengchao/`），帮助 AI 会话路由项目记忆、保存业务意图和开发证据。总体设计见 `docs/DESIGN.md`（先读它，特别是第五部分设计红线）。

## 常用命令

无构建、无 lint、零第三方依赖（`fengchao.py` 刻意只用 Python 标准库，保证目标项目无需安装任何依赖——修改时必须维持这一约束）。

```bash
# 运行全部测试（在仓库根目录）
python3 -m unittest discover -s tests -v

# 运行单个测试类
python3 -m unittest tests.test_fengchao_cli.DeltaMergeTests -v

# 修改内联模板后必须重新生成 templates/ 与 adapters/（CI 校验一致性）
python3 skills/fengchao-business-memory/scripts/fengchao.py export-templates --out .

# 手动验证 CLI（在临时目录中执行，避免污染本仓库）
python3 skills/fengchao-business-memory/scripts/fengchao.py --help
```

测试通过 `subprocess` 在临时目录中调用真实 CLI，属于端到端测试，不 mock；纯函数（路由打分、语义合并）直接 import 单测。

## 核心架构

### 唯一逻辑入口：`fengchao.py`

所有逻辑集中在 `skills/fengchao-business-memory/scripts/fengchao.py`（单文件 CLI，含 `__version__`，与 `pyproject.toml` 版本同步，CI 校验）。同目录的 `check_links.py`、`inspect_project.py`、`check_required_updates.py`、`next_record_name.py` 只是兼容性薄包装；两个 `__init__.py` 仅用于 PyPI 打包。

CLI 子命令与记忆写入的对应关系（核心业务规则）：

| 子命令 | 写入 | 语义 |
|--------|------|------|
| `init` | 全部脚手架 | `--agents` 选 surface；`--memory-only` 只建记忆；默认注册 Claude Code hooks |
| `fengwang --query` | 只读 | 词级打分 + IDF + 时间衰减路由，输出有 4KB 字节预算 |
| `plan` / `conversation` | 参考层 + memory-map | 历史参考，**不是**当前业务事实 |
| `maintain` | 证据层（分档） | lite（无 `--business-change`）只写 changelog；full 走 task-record + **B4 语义合并**（`--change-kind added/modified/removed` + `--rule-name` 稳定 key，先验证后写入，失败不留半成品） |
| `check` | 只读 | `--warn` 恒 0 / `--strict` 要求 git 变更当天有 changelog / `--format json` 诊断信封（code 登记于 DESIGN.md 附录 C） |
| `enable/disable/uninstall/status` | 生命周期 | disable→enable 逐字节还原；uninstall 永不碰记忆根 |
| `hook session-start/stop-gate` | 只读 + `.fengchao/tmp/` 防重标记 | B1 硬门禁，hook_mode: remind/strict/off |
| `migrate/archive/compact/plan-status/doctor/upgrade` | 维护类 | 全部不改写记忆内容语义（红线 5、8） |

CLI 以**当前工作目录**为目标项目根，配置读 `.fengchao/config.yaml`（手写逐行解析，只支持扁平 `key: "value"`）。`memory_root` 键缺失 = 老布局（兼容读取，`migrate` 迁移）。

### 关键不变量（改代码前必读）

1. **真相层唯一现行原则（红线 9）**：domain 文件同一规则名同一时刻只能有一个现行条目，所有写入必须走 `merge_domain_rule()`，禁止绕过合并直接追加。
2. **先验证后写入**：maintain 的合并失败必须发生在任何落盘之前。
3. **卸载对称性（红线 6）**：新增任何宿主写入时，必须同步加入 `remove_host_injections()` 的摘除路径，并保证 disable→enable 逐字节还原（有测试）。
4. **模板唯一事实源（D1）**：生成产物只改 `fengchao.py` 内联模板函数，`templates/`、`adapters/` 是 `export-templates` 的生成物，勿手改。
5. 新增诊断必须先在 `docs/DESIGN.md` 附录 C 登记 code。

### Skill 分发结构

`skills/fengchao-business-memory/` 是完整可分发单元：`SKILL.md`（Agent 入口）+ `references/`（各模式规则，**这是本项目的护城河 prompt 资产**，含 `extraction-quality.md` 强制自检清单）+ `scripts/`。`init` 把该目录复制到目标项目 `.fengchao/skill/`（唯一副本）；各 agent 目录只放薄入口/薄命令（路径常量 `AGENT_COMMAND_PATHS`，注释里有各工具约定的核实记录）。

## Dogfooding

本仓库自身用 FengChao 记录开发（`init --memory-only` 布局，见 `fengchao/`）。每次真实交付后用 `maintain` 记录；规划用 `plan` 记录。这既是活示例也是验收要求。

## 内容语言约定

生成的记忆产物默认中文（`language: zh-CN`，`--language en` 有英文模板集）；代码标识符用英文、注释中文；测试断言依赖模板文案，改动措辞需同步测试。
