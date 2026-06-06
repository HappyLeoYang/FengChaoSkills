#!/usr/bin/env python3
"""FengChao project memory CLI.

This script intentionally uses only the Python standard library so a target
project can run the memory checks without installing dependencies.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONTEXT_DIR = "business-context"
DEFAULT_TASK_DIR = "task-records"
DEFAULT_CHANGELOG_DIR = "changelog"
DEFAULT_PLAN_DIR = "plan-records"
DEFAULT_CONVERSATION_DIR = "conversation-records"
DEFAULT_FENGWANG_DIR = "fengwang"
PROJECT_SKILL_PATH = ".opencode/skills/fengchao-business-memory"
PROJECT_SKILL_PATHS = [
    ".opencode/skills/fengchao-business-memory",
    ".claude/skills/fengchao-business-memory",
    ".cursor/skills/fengchao-business-memory",
    ".codex/skills/fengchao-business-memory",
    ".agents/skills/fengchao-business-memory",
]


@dataclass(frozen=True)
class ProjectConfig:
    project_name: str
    context_dir: str = DEFAULT_CONTEXT_DIR
    task_dir: str = DEFAULT_TASK_DIR
    changelog_dir: str = DEFAULT_CHANGELOG_DIR
    plan_dir: str = DEFAULT_PLAN_DIR
    conversation_dir: str = DEFAULT_CONVERSATION_DIR
    fengwang_dir: str = DEFAULT_FENGWANG_DIR
    language: str = "zh-CN"
    store_conversation: str = "summary-only"
    plan_capture_policy: str = "final-plan-only"


def today() -> str:
    return dt.date.today().isoformat()


def now_minutes() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[\\/:\*\?\"<>\|\n\r]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "untitled"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    return True


def append_once(path: Path, marker: str, content: str) -> bool:
    existing = read_text(path)
    if marker in existing:
        return False
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write(content)
    return True


def load_config(project: Path) -> ProjectConfig:
    config_path = project / ".fengchao" / "config.yaml"
    if not config_path.exists():
        return ProjectConfig(project_name=project.name)

    values: dict[str, str] = {}
    for raw in config_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        values[key.strip()] = value.strip().strip('"')

    return ProjectConfig(
        project_name=values.get("project_name", project.name),
        context_dir=values.get("context_dir", DEFAULT_CONTEXT_DIR),
        task_dir=values.get("task_dir", DEFAULT_TASK_DIR),
        changelog_dir=values.get("changelog_dir", DEFAULT_CHANGELOG_DIR),
        plan_dir=values.get("plan_dir", DEFAULT_PLAN_DIR),
        conversation_dir=values.get("conversation_dir", DEFAULT_CONVERSATION_DIR),
        fengwang_dir=values.get("fengwang_dir", DEFAULT_FENGWANG_DIR),
        language=values.get("language", "zh-CN"),
        store_conversation=values.get("store_conversation", "summary-only"),
        plan_capture_policy=values.get("plan_capture_policy", "final-plan-only"),
    )


def dump_config(config: ProjectConfig) -> str:
    return "\n".join(
        [
            "# FengChaoSkills project memory configuration",
            f'project_name: "{config.project_name}"',
            f'context_dir: "{config.context_dir}"',
            f'task_dir: "{config.task_dir}"',
            f'changelog_dir: "{config.changelog_dir}"',
            f'plan_dir: "{config.plan_dir}"',
            f'conversation_dir: "{config.conversation_dir}"',
            f'fengwang_dir: "{config.fengwang_dir}"',
            f'language: "{config.language}"',
            f'store_conversation: "{config.store_conversation}"',
            f'plan_capture_policy: "{config.plan_capture_policy}"',
            'trigger_policy: "after-real-development-only"',
            "",
        ]
    )


def context_index_template(config: ProjectConfig) -> str:
    return f"""# {config.project_name} 渐进式上下文入口

> 本文件是 AI 理解项目业务上下文的第一入口。普通讨论、Plan 模式、只读分析不会更新本体系；只有实际开发交付后才维护。
> 最后更新：{today()}

## 项目定位

待补充：用一句话描述本项目服务的业务、用户和核心流程。

## 阅读路径

1. 新会话先读取 `../{config.fengwang_dir}/FENGWANG.md` 和 `../{config.fengwang_dir}/memory-map.md`，按需求路由到最小必要上下文。
2. 先读本文件，建立项目全局业务地图。
3. 按需求所属领域读取 `domains/domain-*.md`。
4. 涉及跨模块影响时读取 `impact-matrix.md`。
5. 涉及数据结构时读取 `data/` 下的文档。
6. 需要追溯历史时读取 `../{config.task_dir}/TASK-INDEX.md`、`../{config.plan_dir}/PLAN-INDEX.md`、`../{config.conversation_dir}/CONVERSATION-INDEX.md` 和 `../{config.changelog_dir}/CHANGELOG-INDEX.md`。

## 领域索引

| 领域 | 文档 | 状态 |
|------|------|------|
| 待识别 | `domains/domain-general.md` | 初始化 |

## 关键业务链路

待补充：用 Mermaid 或短列表描述项目主业务链路。

## 变更维护规则

- 实际开发完成后必须生成不可变任务记录和 changelog。
- 只有稳定、已落地的业务事实才能合并进 `business-context/`。
- 每条当前业务认知都应能追溯到任务记录或 changelog。
"""


def domain_template(project_name: str, domain: str = "general") -> str:
    return f"""# {domain} 领域上下文

## 领域定位

待补充：描述该领域在 {project_name} 中负责的业务问题。

## 当前业务规则

- 初始化占位：后续实际开发任务完成后，把稳定业务事实合并到这里。

## 核心入口

| 类型 | 路径/接口 | 说明 |
|------|-----------|------|
| 待补充 | 待补充 | 待补充 |

## 上下游关系

待补充：记录该领域依赖谁、影响谁。

## 关联任务记录

暂无。
"""


def impact_matrix_template() -> str:
    return """# 变更影响矩阵

> 格式：如果改 X，需要检查 Y。实际开发任务完成后按稳定事实增量维护。

| 如果变更 | 需要检查 |
|----------|----------|
| 待补充 | 待补充 |
"""


def debt_registry_template() -> str:
    return """# 技术债务与历史坑点登记

> 只记录已确认的现状、风险和来源，不把讨论中的猜测写入当前业务真相。

| 编号 | 领域 | 现状 | 风险 | 来源 |
|------|------|------|------|------|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
"""


def task_index_template() -> str:
    return f"""# 任务记录索引

> 不可变任务记录的渐进式入口。记录实际开发交付后的业务意图、最终方案和实现证据。
> 最后更新：{today()}

## 最近任务

| 日期 | 领域 | 任务 | 业务变化 | 记录 |
|------|------|------|----------|------|
"""


def changelog_index_template() -> str:
    return f"""# Changelog 索引

> changelog 的渐进式入口。用于按时间、领域、风险、接口和数据变化快速定位历史变更。
> 最后更新：{today()}

## 最近变更

| 日期 | 领域 | 变更 | 类型 | 记录 |
|------|------|------|------|------|

## 按领域索引

| 领域 | 最近记录 |
|------|----------|
"""


def plan_index_template() -> str:
    return f"""# Plan 记录索引

> 计划、方案和待实现设计的渐进式入口。Plan 不是已落地业务事实，不能直接当作当前业务真相。
> 最后更新：{today()}

## 最近计划

| 日期 | 领域 | 状态 | 计划 | 记录 |
|------|------|------|------|------|
"""


def conversation_index_template() -> str:
    return f"""# 对话上下文索引

> 用户业务解释、偏好、术语、边界和否定方案的渐进式入口。默认只保存萃取摘要，不保存完整对话。
> 最后更新：{today()}

## 最近对话记忆

| 日期 | 领域 | 主题 | 建议提升 | 记录 |
|------|------|------|----------|------|
"""


def fengwang_template(config: ProjectConfig) -> str:
    return f"""# FengWang 蜂王入口

> 本文件是新 AI 会话理解 {config.project_name} 的统一入口。先读本文件，再按 `memory-map.md` 路由到最小必要上下文。
> 最后更新：{today()}

## 记忆分层

| 类型 | 目录 | 语义 |
|------|------|------|
| 当前事实 | `../{config.context_dir}/` | 当前稳定业务真相 |
| 已落地任务 | `../{config.task_dir}/` | 已交付开发任务的业务意图、最终方案和证据 |
| 变更历史 | `../{config.changelog_dir}/` | 已落地代码、配置、数据库等变更历史 |
| 计划方案 | `../{config.plan_dir}/` | Plan 模式或方案阶段产物，不代表已落地事实 |
| 对话记忆 | `../{config.conversation_dir}/` | 用户解释过的业务背景、偏好、术语和边界 |

## 新需求处理流程

1. 读取本文件和 `memory-map.md`。
2. 根据用户需求中的业务词、接口、页面、数据表、状态或权限线索定位相关记录。
3. 优先读取当前事实，再读取相关对话、计划、任务和 changelog。
4. 如果记录冲突，以 `business-context` 为当前事实；`task-records/changelog` 为落地证据；`plan-records/conversation-records` 为历史参考。
5. 不全量读取所有记录，优先读取 FengWang 路由出的 8-12 个文件。

## 维护规则

- Plan 产出后维护 `plan-records/` 和 `memory-map.md`，不写 changelog，不写业务真相。
- 有长期价值的用户业务解释维护 `conversation-records/` 和 `memory-map.md`。
- 真实开发完成后维护 `task-records/`、`changelog/`，必要时更新 `business-context/` 和 `memory-map.md`。
"""


def memory_map_template(config: ProjectConfig) -> str:
    return f"""# FengWang Memory Map

> 按领域、关键词、接口、文件、状态和业务链路维护的渐进式路由表。
> 最后更新：{today()}

| 类型 | 状态 | 领域 | 触发词/线索 | 优先读取 | 说明 |
|------|------|------|-------------|----------|------|
| context | current | general | 项目 上下文 业务 当前事实 | [CONTEXT-INDEX.md](../{config.context_dir}/CONTEXT-INDEX.md) | 当前业务上下文入口 |
| task | historical | general | 任务 开发 落地 实现 | [TASK-INDEX.md](../{config.task_dir}/TASK-INDEX.md) | 已落地任务入口 |
| changelog | historical | general | changelog 变更 历史 代码 | [CHANGELOG-INDEX.md](../{config.changelog_dir}/CHANGELOG-INDEX.md) | 变更历史入口 |
| plan | proposed | general | plan 计划 方案 设计 | [PLAN-INDEX.md](../{config.plan_dir}/PLAN-INDEX.md) | 计划记录入口 |
| conversation | historical | general | 对话 解释 术语 偏好 边界 | [CONVERSATION-INDEX.md](../{config.conversation_dir}/CONVERSATION-INDEX.md) | 对话记忆入口 |
"""


def agents_snippet() -> str:
    return """

<!-- FENGCHAO-BUSINESS-MEMORY:START -->
## FengChaoSkills 业务记忆规则

仅在实际开发任务完成后触发 FengChaoSkills：代码、配置、数据库脚本、接口、文档产物或其他项目文件发生了真实交付变更时才维护。

新会话先读取 `fengwang/FENGWANG.md`，再根据 `fengwang/memory-map.md` 定位最小必要上下文。

本项目内置 FengChaoSkills，项目级 skill 路径如下：

- OpenCode：`.opencode/skills/fengchao-business-memory/SKILL.md`
- Claude Code：`.claude/skills/fengchao-business-memory/SKILL.md`
- Cursor：`.cursor/skills/fengchao-business-memory/SKILL.md`
- Codex：`.codex/skills/fengchao-business-memory/SKILL.md`
- Codex/Agents 兼容：`.agents/skills/fengchao-business-memory/SKILL.md`

不得在普通讨论、Plan 模式、只读分析、代码讲解、需求头脑风暴、未落地方案评审时维护 task-records/changelog。Plan 模式产出最终计划后只维护 `plan-records/`；有长期价值的用户业务解释只维护 `conversation-records/`。

开发完成后、最终汇报前必须执行：

1. 从本轮对话萃取用户真实业务诉求、最终方案、关键决策、实现证据和验证结果。
2. 生成 `task-records/YYYY-MM-DD_NNN_标题.md` 不可变任务记录。
3. 生成 `changelog/YYYY-MM-DD_NNN_标题.md`。
4. 更新 `task-records/TASK-INDEX.md` 与 `changelog/CHANGELOG-INDEX.md`。
5. 如果业务规则、接口契约、数据结构、权限、状态机或核心流程发生稳定变化，更新 `business-context/` 对应领域页和入口索引。
6. 更新 `fengwang/memory-map.md`。
7. 运行 `python .opencode/skills/fengchao-business-memory/scripts/fengchao.py check` 或项目配置中的等价命令。
<!-- FENGCHAO-BUSINESS-MEMORY:END -->
"""


def claude_snippet() -> str:
    return agents_snippet().replace("## FengChaoSkills 业务记忆规则", "## FengChaoSkills Business Memory") + """

Project-local FengChao skill is available at `.claude/skills/fengchao-business-memory/SKILL.md`.
When FengChaoSkills applies, read `.claude/skills/fengchao-business-memory/SKILL.md` and follow it.
"""


def cursor_rule() -> str:
    return """---
description: 实际开发完成后维护 FengChaoSkills 任务记录、changelog 和渐进式业务上下文；讨论、Plan、只读分析不触发。
globs:
alwaysApply: true
---

# FengChaoSkills

当且仅当本次会话完成了真实开发交付，最终回复前必须执行 FengChaoSkills 维护流程。

不触发：普通讨论、Plan 模式、方案评审、只读分析、代码讲解、未修改项目文件的排查。

新会话先读取 `fengwang/FENGWANG.md` 并按 `fengwang/memory-map.md` 路由到最小必要上下文。

项目级 FengChao skill 位于 `.cursor/skills/fengchao-business-memory/SKILL.md`。当 FengChaoSkills 适用时，读取该文件并按其中规则执行。

Plan 模式产出最终计划后只维护 `plan-records/`；长期有价值的用户业务解释只维护 `conversation-records/`；两者默认不直接更新 `business-context/`。

触发后维护：

- `task-records/` 不可变任务记录
- `changelog/` 单次变更记录和索引
- 命中稳定业务变化时更新 `business-context/`
- 更新 `fengwang/memory-map.md`

默认只保存萃取摘要，不保存完整对话。
"""


def opencode_config() -> str:
    return json.dumps(
        {
            "$schema": "https://opencode.ai/config.schema.json",
            "instructions": [
                "AGENTS.md",
                "fengwang/*.md",
                "business-context/**/*.md",
                "plan-records/PLAN-INDEX.md",
                "conversation-records/CONVERSATION-INDEX.md",
                "task-records/TASK-INDEX.md",
                "changelog/CHANGELOG-INDEX.md",
            ],
            "lsp": False,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def install_project_skill(project: Path, target_relative: str) -> str:
    source = Path(__file__).resolve().parents[1]
    target = project / target_relative
    ensure_dir(target.parent)
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )
    return target_relative


def init_project(project: Path, args: argparse.Namespace) -> int:
    config = ProjectConfig(
        project_name=args.project_name or project.name,
        context_dir=args.context_dir,
        task_dir=args.task_dir,
        changelog_dir=args.changelog_dir,
        plan_dir=args.plan_dir,
        conversation_dir=args.conversation_dir,
        fengwang_dir=args.fengwang_dir,
    )

    created: list[str] = []
    paths = [
        project / ".fengchao",
        project / config.context_dir / "domains",
        project / config.context_dir / "architecture",
        project / config.context_dir / "data",
        project / config.task_dir,
        project / config.changelog_dir,
        project / config.plan_dir,
        project / config.conversation_dir,
        project / config.fengwang_dir,
        project / ".opencode" / "skills",
        project / ".claude" / "skills",
        project / ".cursor" / "skills",
        project / ".codex" / "skills",
        project / ".agents" / "skills",
        project / ".cursor" / "rules",
    ]
    for path in paths:
        ensure_dir(path)

    files = {
        project / ".fengchao" / "config.yaml": dump_config(config),
        project / config.context_dir / "CONTEXT-INDEX.md": context_index_template(config),
        project / config.context_dir / "domains" / "domain-general.md": domain_template(
            config.project_name
        ),
        project / config.context_dir / "impact-matrix.md": impact_matrix_template(),
        project / config.context_dir / "debt-registry.md": debt_registry_template(),
        project / config.task_dir / "TASK-INDEX.md": task_index_template(),
        project / config.changelog_dir / "CHANGELOG-INDEX.md": changelog_index_template(),
        project / config.plan_dir / "PLAN-INDEX.md": plan_index_template(),
        project / config.conversation_dir / "CONVERSATION-INDEX.md": conversation_index_template(),
        project / config.fengwang_dir / "FENGWANG.md": fengwang_template(config),
        project / config.fengwang_dir / "memory-map.md": memory_map_template(config),
        project / ".cursor" / "rules" / "fengchao.mdc": cursor_rule(),
        project / "CLAUDE.md": claude_snippet().lstrip(),
        project / "opencode.json": opencode_config(),
    }
    for path, content in files.items():
        if write_if_missing(path, content):
            created.append(str(path.relative_to(project)))

    if append_once(project / "AGENTS.md", "FENGCHAO-BUSINESS-MEMORY:START", agents_snippet()):
        created.append("AGENTS.md")

    for skill_path in PROJECT_SKILL_PATHS:
        created.append(install_project_skill(project, skill_path))

    print("FengChao initialized")
    for path in created:
        print(f"created {path}")
    return 0


def next_record_path(directory: Path, title: str) -> Path:
    date = today()
    existing = sorted(directory.glob(f"{date}_*.md"))
    seq = len(existing) + 1
    return directory / f"{date}_{seq:03d}_{slugify(title)}.md"


def optional_list(values: list[str] | None) -> list[str]:
    return [value for value in (values or []) if value.strip()]


def link_list(paths: list[str] | None) -> str:
    items = optional_list(paths)
    if not items:
        return "- 无"
    return "\n".join(f"- `{item}`" for item in items)


def project_relative_link_list(paths: list[str] | None) -> str:
    items = optional_list(paths)
    if not items:
        return "- 无"
    rows: list[str] = []
    for item in items:
        target = item if item.startswith("../") else f"../{item}"
        rows.append(f"- [{item}]({target})")
    return "\n".join(rows)


def task_record_content(args: argparse.Namespace, changelog_name: str) -> str:
    changed_files = optional_list(args.changed_file)
    evidence = optional_list(args.evidence)
    validation = optional_list(args.validation)
    return f"""# {args.title}

- **记录时间**：{now_minutes()}
- **领域**：{args.domain}
- **隐私策略**：只保存对话萃取摘要，不保存完整对话
- **关联 changelog**：`../changelog/{changelog_name}`
- **关联 plan**：
{project_relative_link_list(args.from_plan)}
- **关联 conversation**：
{project_relative_link_list(args.from_conversation)}

## 用户真实业务诉求

{args.summary}

## 最终确认的业务规则

{args.business_change or "本次没有稳定业务规则变化。"}

## 最终实现方案

{args.implementation}

## 关键决策与取舍

{args.decision or "本次未记录额外取舍。"}

## 涉及范围

| 类型 | 内容 |
|------|------|
| 领域 | `{args.domain}` |
| 文件 | {", ".join(f"`{item}`" for item in changed_files) if changed_files else "未记录"} |

## 实现证据

{bullet_list(evidence) if evidence else "- 未记录"}

## 验证结果

{bullet_list(validation) if validation else "- 未记录"}

## 后续风险或待确认点

{args.risk or "暂无。"}
"""


def changelog_content(args: argparse.Namespace, task_name: str) -> str:
    changed_files = optional_list(args.changed_file)
    return f"""# {args.title}

- **变更时间**：{now_minutes()}
- **领域**：{args.domain}
- **变更类型**：{args.change_type}
- **关联任务记录**：`../task-records/{task_name}`

## 变更概述

{args.summary}

## 业务变化

{args.business_change or "本次没有稳定业务规则变化。"}

## 实现说明

{args.implementation}

## 涉及文件

{bullet_list(changed_files) if changed_files else "- 未记录"}

## 验证

{bullet_list(optional_list(args.validation)) if args.validation else "- 未记录"}
"""


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def update_task_index(index: Path, args: argparse.Namespace, task_path: Path) -> None:
    row = (
        f"| {today()} | `{args.domain}` | {args.title} | "
        f"{args.business_change or '无稳定业务变化'} | "
        f"[{task_path.name}]({task_path.name}) |\n"
    )
    append_index_row(index, row)


def update_changelog_index(index: Path, args: argparse.Namespace, changelog_path: Path) -> None:
    row = (
        f"| {today()} | `{args.domain}` | {args.title} | `{args.change_type}` | "
        f"[{changelog_path.name}]({changelog_path.name}) |\n"
    )
    append_index_row(index, row)
    domain_marker = f"| `{args.domain}` |"
    existing = read_text(index)
    if domain_marker not in existing:
        append_once(
            index,
            domain_marker,
            f"| `{args.domain}` | [{changelog_path.name}]({changelog_path.name}) |\n",
        )


def append_index_row(index: Path, row: str) -> None:
    existing = read_text(index)
    if row in existing:
        return
    with index.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write(row)


def update_domain_context(project: Path, config: ProjectConfig, args: argparse.Namespace, task_path: Path) -> None:
    if not args.business_change:
        return
    domain_path = project / config.context_dir / "domains" / f"domain-{slugify(args.domain)}.md"
    if not domain_path.exists():
        write_if_missing(domain_path, domain_template(config.project_name, args.domain))
    entry = f"""

## {today()} 已落地业务事实

- **任务**：[{args.title}](../../{config.task_dir}/{task_path.name})
- **规则**：{args.business_change}
- **实现摘要**：{args.implementation}
"""
    append_once(domain_path, f"[{args.title}](../../{config.task_dir}/{task_path.name})", entry)


def memory_map_link(record_path: Path, base_dir: Path) -> str:
    label = record_path.name
    return f"[{label}]({os.path.relpath(record_path, base_dir)})"


def collect_keywords(*parts: str, extra: list[str] | None = None) -> str:
    words: list[str] = []
    for part in parts:
        words.extend(re.findall(r"[\w\u4e00-\u9fff]+", part or ""))
    words.extend(optional_list(extra))
    seen: list[str] = []
    for word in words:
        if word and word not in seen:
            seen.append(word)
    return " ".join(seen[:20]) or "general"


def update_memory_map(
    project: Path,
    config: ProjectConfig,
    *,
    record_type: str,
    status: str,
    domain: str,
    keywords: str,
    record_path: Path,
    description: str,
) -> None:
    memory_map = project / config.fengwang_dir / "memory-map.md"
    if not memory_map.exists():
        write_if_missing(memory_map, memory_map_template(config))
    link = memory_map_link(record_path, memory_map.parent)
    row = f"| {record_type} | {status} | {domain} | {keywords} | {link} | {description} |\n"
    append_index_row(memory_map, row)


def maintain_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    task_dir = project / config.task_dir
    changelog_dir = project / config.changelog_dir
    ensure_dir(task_dir)
    ensure_dir(changelog_dir)

    task_path = next_record_path(task_dir, args.title)
    changelog_path = next_record_path(changelog_dir, args.title)
    task_path.write_text(task_record_content(args, changelog_path.name), encoding="utf-8")
    changelog_path.write_text(changelog_content(args, task_path.name), encoding="utf-8")

    update_task_index(task_dir / "TASK-INDEX.md", args, task_path)
    update_changelog_index(changelog_dir / "CHANGELOG-INDEX.md", args, changelog_path)
    update_domain_context(project, config, args, task_path)
    update_memory_map(
        project,
        config,
        record_type="task",
        status="implemented",
        domain=args.domain,
        keywords=collect_keywords(args.title, args.summary, args.business_change, args.implementation),
        record_path=task_path,
        description="已落地开发任务",
    )
    update_memory_map(
        project,
        config,
        record_type="changelog",
        status="historical",
        domain=args.domain,
        keywords=collect_keywords(args.title, args.summary, args.business_change, args.implementation),
        record_path=changelog_path,
        description="已落地变更记录",
    )

    print(f"created {task_path.relative_to(project)}")
    print(f"created {changelog_path.relative_to(project)}")
    return 0


def plan_record_content(args: argparse.Namespace) -> str:
    assumptions = optional_list(args.assumption)
    open_questions = optional_list(args.open_question)
    impact = optional_list(args.impact)
    return f"""# {args.title}

- **记录时间**：{now_minutes()}
- **领域**：{args.domain}
- **计划状态**：{args.status}
- **捕获策略**：final-plan-only

## 用户目标

{args.goal}

## 当前理解的业务背景

{args.context or "未记录。"}

## AI 制定的计划

{args.plan}

## 关键假设

{bullet_list(assumptions) if assumptions else "- 无"}

## 待确认问题

{bullet_list(open_questions) if open_questions else "- 无"}

## 预计影响范围

{bullet_list(impact) if impact else "- 未记录"}

## 后续落地链接

- task-records：待落地后补充
- changelog：待落地后补充
"""


def update_plan_index(index: Path, args: argparse.Namespace, plan_path: Path) -> None:
    row = f"| {today()} | `{args.domain}` | `{args.status}` | {args.title} | [{plan_path.name}]({plan_path.name}) |\n"
    append_index_row(index, row)


def plan_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    plan_dir = project / config.plan_dir
    ensure_dir(plan_dir)
    write_if_missing(plan_dir / "PLAN-INDEX.md", plan_index_template())
    plan_path = next_record_path(plan_dir, args.title)
    plan_path.write_text(plan_record_content(args), encoding="utf-8")
    update_plan_index(plan_dir / "PLAN-INDEX.md", args, plan_path)
    update_memory_map(
        project,
        config,
        record_type="plan",
        status=args.status,
        domain=args.domain,
        keywords=collect_keywords(args.title, args.goal, args.plan, extra=args.assumption),
        record_path=plan_path,
        description="计划阶段记录，非当前业务事实",
    )
    print(f"created {plan_path.relative_to(project)}")
    return 0


def conversation_record_content(args: argparse.Namespace) -> str:
    terms = optional_list(args.term)
    preferences = optional_list(args.preference)
    rejected = optional_list(args.rejected)
    unverified = optional_list(args.unverified)
    related = optional_list(args.related)
    return f"""# {args.title}

- **记录时间**：{now_minutes()}
- **领域**：{args.domain}
- **隐私策略**：只保存对话萃取摘要，不保存完整对话
- **建议提升到 business-context**：{args.promote}

## 用户解释的业务背景

{args.summary}

## 业务术语与含义

{bullet_list(terms) if terms else "- 未记录"}

## 用户偏好和约束

{bullet_list(preferences) if preferences else "- 未记录"}

## 用户明确否定的方案

{bullet_list(rejected) if rejected else "- 未记录"}

## 仍未验证或未落地的信息

{bullet_list(unverified) if unverified else "- 未记录"}

## 关联记录

{bullet_list(related) if related else "- 无"}
"""


def update_conversation_index(index: Path, args: argparse.Namespace, conversation_path: Path) -> None:
    row = (
        f"| {today()} | `{args.domain}` | {args.title} | `{args.promote}` | "
        f"[{conversation_path.name}]({conversation_path.name}) |\n"
    )
    append_index_row(index, row)


def conversation_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    conversation_dir = project / config.conversation_dir
    ensure_dir(conversation_dir)
    write_if_missing(conversation_dir / "CONVERSATION-INDEX.md", conversation_index_template())
    conversation_path = next_record_path(conversation_dir, args.title)
    conversation_path.write_text(conversation_record_content(args), encoding="utf-8")
    update_conversation_index(conversation_dir / "CONVERSATION-INDEX.md", args, conversation_path)
    update_memory_map(
        project,
        config,
        record_type="conversation",
        status="historical",
        domain=args.domain,
        keywords=collect_keywords(args.title, args.summary, extra=args.term + args.preference + args.rejected),
        record_path=conversation_path,
        description="用户业务解释和偏好，非当前业务事实",
    )
    print(f"created {conversation_path.relative_to(project)}")
    return 0


def inspect_project(project: Path, args: argparse.Namespace) -> int:
    files = []
    for path in project.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            files.append(path.relative_to(project))
    print(f"Project: {project.name}")
    print(f"Files: {len(files)}")
    for candidate in ["package.json", "pom.xml", "pyproject.toml", "go.mod", "Cargo.toml"]:
        if (project / candidate).exists():
            print(f"Detected manifest: {candidate}")
    for path in sorted(files)[: args.limit]:
        print(path)
    return 0


def score_memory_row(query_terms: list[str], row: str) -> int:
    lowered = row.lower()
    score = 0
    for term in query_terms:
        if term and term.lower() in lowered:
            score += 1
    if "| context |" in lowered:
        score += 2
    elif "| conversation |" in lowered:
        score += 1
    elif "| plan |" in lowered:
        score += 1
    return score


def extract_markdown_link_target(row: str) -> str:
    match = LINK_RE.search(row)
    return match.group(1) if match else ""


def fengwang_query(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    memory_map = project / config.fengwang_dir / "memory-map.md"
    if not memory_map.exists():
        print(f"Missing {memory_map.relative_to(project)}", file=sys.stderr)
        return 1
    query_terms = re.findall(r"[\w\u4e00-\u9fff]+", args.query)
    rows = [
        row
        for row in read_text(memory_map).splitlines()
        if row.startswith("|") and not row.startswith("| 类型") and not row.startswith("|------")
    ]
    scored: list[tuple[int, str]] = []
    for row in rows:
        score = score_memory_row(query_terms, row)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    print("FengWang suggested context:")
    for idx, (_, row) in enumerate(scored[: args.limit], start=1):
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        record_type = cells[0] if len(cells) > 0 else "unknown"
        domain = cells[2] if len(cells) > 2 else "unknown"
        target = extract_markdown_link_target(row)
        description = cells[5] if len(cells) > 5 else ""
        print(f"{idx}. {target} — {record_type}/{domain} — {description}")
    if not scored:
        print("No direct match. Read fengwang/FENGWANG.md and business-context/CONTEXT-INDEX.md first.")
    return 0


LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|#|mailto:)([^)]+)\)")


def check_links(root: Path, markdown_file: Path) -> list[str]:
    errors: list[str] = []
    text = read_text(markdown_file)
    for link in LINK_RE.findall(text):
        target = link.split("#", 1)[0].strip()
        if not target or target.startswith("<"):
            continue
        target_path = (markdown_file.parent / target).resolve()
        try:
            target_path.relative_to(root.resolve())
        except ValueError:
            continue
        if not target_path.exists():
            errors.append(
                f"Broken link in {markdown_file.relative_to(root)}: {link} -> {target_path.relative_to(root)}"
            )
    return errors


def git_changed_files(project: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    changed: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        changed.append(line[3:].strip())
    return changed


def check_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    required = [
        project / ".fengchao" / "config.yaml",
        project / config.fengwang_dir / "FENGWANG.md",
        project / config.fengwang_dir / "memory-map.md",
        project / config.context_dir / "CONTEXT-INDEX.md",
        project / config.plan_dir / "PLAN-INDEX.md",
        project / config.conversation_dir / "CONVERSATION-INDEX.md",
        project / config.task_dir / "TASK-INDEX.md",
        project / config.changelog_dir / "CHANGELOG-INDEX.md",
    ]
    errors: list[str] = []
    for path in required:
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(project)}")

    for directory in [
        project / config.fengwang_dir,
        project / config.context_dir,
        project / config.plan_dir,
        project / config.conversation_dir,
        project / config.task_dir,
        project / config.changelog_dir,
    ]:
        if not directory.exists():
            continue
        for markdown_file in directory.rglob("*.md"):
            errors.extend(check_links(project, markdown_file))

    if args.require_records_for_git_changes:
        changed = git_changed_files(project)
        project_changes = [
            item
            for item in changed
            if not item.startswith((config.task_dir + "/", config.changelog_dir + "/", config.context_dir + "/"))
        ]
        if project_changes and not list((project / config.task_dir).glob(f"{today()}_*.md")):
            errors.append("Git changes detected but no task record exists for today")
        if project_changes and not list((project / config.changelog_dir).glob(f"{today()}_*.md")):
            errors.append("Git changes detected but no changelog exists for today")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("FengChao check passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain FengChao project memory artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Initialize FengChao memory artifacts in a project.")
    init.add_argument("--project-name", default=None)
    init.add_argument("--context-dir", default=DEFAULT_CONTEXT_DIR)
    init.add_argument("--task-dir", default=DEFAULT_TASK_DIR)
    init.add_argument("--changelog-dir", default=DEFAULT_CHANGELOG_DIR)
    init.add_argument("--plan-dir", default=DEFAULT_PLAN_DIR)
    init.add_argument("--conversation-dir", default=DEFAULT_CONVERSATION_DIR)
    init.add_argument("--fengwang-dir", default=DEFAULT_FENGWANG_DIR)
    init.set_defaults(func=init_project)

    maintain = subparsers.add_parser("maintain", help="Create task/changelog records after real development.")
    maintain.add_argument("--title", required=True)
    maintain.add_argument("--summary", required=True)
    maintain.add_argument("--implementation", required=True)
    maintain.add_argument("--business-change", default="")
    maintain.add_argument("--decision", default="")
    maintain.add_argument("--risk", default="")
    maintain.add_argument("--domain", default="general")
    maintain.add_argument("--change-type", default="development")
    maintain.add_argument("--changed-file", action="append")
    maintain.add_argument("--evidence", action="append")
    maintain.add_argument("--validation", action="append")
    maintain.add_argument("--from-plan", action="append")
    maintain.add_argument("--from-conversation", action="append")
    maintain.set_defaults(func=maintain_project)

    plan = subparsers.add_parser("plan", help="Create a plan record without changing business truth.")
    plan.add_argument("--title", required=True)
    plan.add_argument("--domain", default="general")
    plan.add_argument("--goal", required=True)
    plan.add_argument("--plan", required=True)
    plan.add_argument("--context", default="")
    plan.add_argument("--assumption", action="append")
    plan.add_argument("--open-question", action="append")
    plan.add_argument("--impact", action="append")
    plan.add_argument(
        "--status",
        default="proposed",
        choices=["proposed", "approved", "superseded", "implemented", "abandoned"],
    )
    plan.set_defaults(func=plan_project)

    conversation = subparsers.add_parser(
        "conversation", help="Create a conversation memory record without changing business truth."
    )
    conversation.add_argument("--title", required=True)
    conversation.add_argument("--domain", default="general")
    conversation.add_argument("--summary", required=True)
    conversation.add_argument("--term", action="append", default=[])
    conversation.add_argument("--preference", action="append", default=[])
    conversation.add_argument("--rejected", action="append", default=[])
    conversation.add_argument("--unverified", action="append", default=[])
    conversation.add_argument("--related", action="append")
    conversation.add_argument("--promote", default="no", choices=["no", "candidate", "confirmed"])
    conversation.set_defaults(func=conversation_project)

    fengwang = subparsers.add_parser("fengwang", help="Route a user request to relevant memory files.")
    fengwang.add_argument("--query", required=True)
    fengwang.add_argument("--limit", type=int, default=12)
    fengwang.set_defaults(func=fengwang_query)

    inspect = subparsers.add_parser("inspect", help="Inspect project files without mutating them.")
    inspect.add_argument("--limit", type=int, default=80)
    inspect.set_defaults(func=inspect_project)

    check = subparsers.add_parser("check", help="Validate FengChao artifacts and links.")
    check.add_argument("--require-records-for-git-changes", action="store_true")
    check.set_defaults(func=check_project)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path(os.getcwd()).resolve()
    return args.func(project, args)


if __name__ == "__main__":
    raise SystemExit(main())
