#!/usr/bin/env python3
"""FengChao 项目业务记忆 CLI。

单文件、零第三方依赖（设计红线 1）：目标项目无需安装任何东西即可运行。
本文件内联模板是所有生成产物的唯一事实源（DESIGN.md D1），仓库中的
templates/ 与 adapters/ 由 `export-templates` 子命令生成，勿手改。
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

__version__ = "0.3.0"

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

DEFAULT_MEMORY_ROOT = "fengchao"
DEFAULT_CONTEXT_DIR = "business-context"
DEFAULT_TASK_DIR = "task-records"
DEFAULT_CHANGELOG_DIR = "changelog"
DEFAULT_PLAN_DIR = "plan-records"
DEFAULT_CONVERSATION_DIR = "conversation-records"
DEFAULT_FENGWANG_DIR = "fengwang"

SKILL_INSTALL_DIR = ".fengchao/skill"
CLI_RELATIVE = ".fengchao/skill/scripts/fengchao.py"

MARKER_START = "<!-- FENGCHAO-BUSINESS-MEMORY:START -->"
MARKER_END = "<!-- FENGCHAO-BUSINESS-MEMORY:END -->"
SHELL_MARKER_START = "# FENGCHAO-BUSINESS-MEMORY:START"
SHELL_MARKER_END = "# FENGCHAO-BUSINESS-MEMORY:END"

AGENT_CHOICES = ("claude", "cursor", "codex", "opencode", "agents")
COMMAND_VERBS = ("route", "remember", "status")

# 各工具项目级斜杠命令目录约定（2026-07-08 逐一核实，A4 要求落地时核实后写入注释）：
# - Claude Code：`.claude/commands/fengchao/<verb>.md` → 呈现为 /fengchao:<verb>；
#   支持 frontmatter description 与 $ARGUMENTS 占位符。
# - Cursor：`.cursor/commands/<name>.md`（项目级、纯 Markdown、无 frontmatter），
#   文件名即命令名 → /fengchao-<verb>。
# - OpenCode：`.opencode/commands/<name>.md`（复数目录），frontmatter description，
#   支持 $ARGUMENTS。
# - Codex：自定义 prompts 仅支持全局 ~/.codex/prompts（官方已标记 deprecated），
#   无项目级约定 → 不生成薄命令，回退 AGENTS.md marker 块。
AGENT_COMMAND_PATHS = {
    "claude": ".claude/commands/fengchao/{verb}.md",
    "cursor": ".cursor/commands/fengchao-{verb}.md",
    "opencode": ".opencode/commands/fengchao-{verb}.md",
}

# 记录文件命名：YYYY-MM-DD_NNN_标题slug.md
RECORD_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{3})_.+\.md$")
LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|#|mailto:)([^)]+)\)")
RULE_HEADING_RE = re.compile(r"^###\s+(?:规则：|Rule:\s*)(.+?)\s*$")
FACT_HEADING_RE = re.compile(r"^###\s+(?:事实：|Fact:\s*)(.+?)\s*$")
LEGACY_CONTEXT_ENTRY_RE = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}\s+已落地业务事实\s*$")

CURRENT_RULES_TITLES = ("## 当前业务规则", "## Current Business Rules")
RETIRED_RULES_TITLES = ("## 已废除规则", "## Retired Rules")
CURRENT_FACTS_TITLES = ("## 现行事实", "## Current Facts")
RETIRED_FACTS_TITLES = ("## 已失效事实", "## Retired Facts")
PROJECT_FACTS_FILE = "project-facts.md"

# C1 预算管制：memory-map 单行 keywords 列字符上限 / fengwang 输出字节预算
KEYWORDS_MAX_CHARS = 120
DEFAULT_ROUTE_BUDGET_BYTES = 4096

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_CANCELLED = 130


# ---------------------------------------------------------------------------
# 配置与布局
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProjectConfig:
    project_name: str
    # memory_root 为空字符串表示老布局（六目录散在项目根下）
    memory_root: str = DEFAULT_MEMORY_ROOT
    context_dir: str = DEFAULT_CONTEXT_DIR
    task_dir: str = DEFAULT_TASK_DIR
    changelog_dir: str = DEFAULT_CHANGELOG_DIR
    plan_dir: str = DEFAULT_PLAN_DIR
    conversation_dir: str = DEFAULT_CONVERSATION_DIR
    fengwang_dir: str = DEFAULT_FENGWANG_DIR
    language: str = "zh-CN"
    store_conversation: str = "summary-only"
    plan_capture_policy: str = "final-plan-only"
    enabled: bool = True
    agents: tuple = ()
    hook_mode: str = "remind"
    with_hooks: bool = True
    installed_version: str = ""


@dataclass(frozen=True)
class Layout:
    """把配置解析成一组绝对路径，屏蔽新老布局差异。"""

    project: Path
    memory_root: Path
    fengwang_dir: Path
    context_dir: Path
    task_dir: Path
    changelog_dir: Path
    plan_dir: Path
    conversation_dir: Path
    is_legacy: bool

    def record_dirs(self) -> "list[tuple[str, Path]]":
        return [
            ("task", self.task_dir),
            ("changelog", self.changelog_dir),
            ("plan", self.plan_dir),
            ("conversation", self.conversation_dir),
        ]

    def memory_dirs(self) -> "list[Path]":
        return [
            self.fengwang_dir,
            self.context_dir,
            self.task_dir,
            self.changelog_dir,
            self.plan_dir,
            self.conversation_dir,
        ]


def today() -> str:
    return dt.date.today().isoformat()


def now_minutes() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def is_en(config: ProjectConfig) -> bool:
    return config.language.strip().lower().startswith("en")


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


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    write_text(path, content)
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


def parse_bool(value: str, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() not in ("false", "0", "no", "off")


def detect_legacy_layout(project: Path) -> bool:
    """无配置文件时的老布局启发式：fengwang/FENGWANG.md 在根下且新记忆根不存在。"""
    legacy_marker = project / DEFAULT_FENGWANG_DIR / "FENGWANG.md"
    new_marker = project / DEFAULT_MEMORY_ROOT / "FENGWANG.md"
    return legacy_marker.exists() and not new_marker.exists()


def load_config(project: Path) -> ProjectConfig:
    config_path = project / ".fengchao" / "config.yaml"
    if not config_path.exists():
        memory_root = "" if detect_legacy_layout(project) else DEFAULT_MEMORY_ROOT
        return ProjectConfig(project_name=project.name, memory_root=memory_root)

    values: "dict[str, str]" = {}
    for raw in config_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        values[key.strip()] = value.strip().strip('"')

    agents = tuple(a.strip() for a in values.get("agents", "").split(",") if a.strip())
    return ProjectConfig(
        project_name=values.get("project_name", project.name),
        # 老配置没有 memory_root 键 → 老布局
        memory_root=values.get("memory_root", ""),
        context_dir=values.get("context_dir", DEFAULT_CONTEXT_DIR),
        task_dir=values.get("task_dir", DEFAULT_TASK_DIR),
        changelog_dir=values.get("changelog_dir", DEFAULT_CHANGELOG_DIR),
        plan_dir=values.get("plan_dir", DEFAULT_PLAN_DIR),
        conversation_dir=values.get("conversation_dir", DEFAULT_CONVERSATION_DIR),
        fengwang_dir=values.get("fengwang_dir", DEFAULT_FENGWANG_DIR),
        language=values.get("language", "zh-CN"),
        store_conversation=values.get("store_conversation", "summary-only"),
        plan_capture_policy=values.get("plan_capture_policy", "final-plan-only"),
        enabled=parse_bool(values.get("enabled", "true")),
        agents=agents,
        hook_mode=values.get("hook_mode", "remind"),
        with_hooks=parse_bool(values.get("with_hooks", "true")),
        installed_version=values.get("installed_version", ""),
    )


def dump_config(config: ProjectConfig) -> str:
    return "\n".join(
        [
            "# FengChaoSkills project memory configuration",
            f'project_name: "{config.project_name}"',
            f'memory_root: "{config.memory_root}"',
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
            f'enabled: "{"true" if config.enabled else "false"}"',
            f'agents: "{",".join(config.agents)}"',
            f'hook_mode: "{config.hook_mode}"',
            f'with_hooks: "{"true" if config.with_hooks else "false"}"',
            f'installed_version: "{config.installed_version}"',
            "",
        ]
    )


def save_config(project: Path, config: ProjectConfig) -> None:
    write_text(project / ".fengchao" / "config.yaml", dump_config(config))


def resolve_layout(project: Path, config: ProjectConfig) -> Layout:
    if config.memory_root:
        root = project / config.memory_root
        return Layout(
            project=project,
            memory_root=root,
            fengwang_dir=root,
            context_dir=root / config.context_dir,
            task_dir=root / config.task_dir,
            changelog_dir=root / config.changelog_dir,
            plan_dir=root / config.plan_dir,
            conversation_dir=root / config.conversation_dir,
            is_legacy=False,
        )
    return Layout(
        project=project,
        memory_root=project,
        fengwang_dir=project / config.fengwang_dir,
        context_dir=project / config.context_dir,
        task_dir=project / config.task_dir,
        changelog_dir=project / config.changelog_dir,
        plan_dir=project / config.plan_dir,
        conversation_dir=project / config.conversation_dir,
        is_legacy=True,
    )


def fengwang_entry_rel(config: ProjectConfig) -> str:
    """FENGWANG.md 相对项目根的展示路径（用于宿主注入文案）。"""
    if config.memory_root:
        return f"{config.memory_root}/FENGWANG.md"
    return f"{config.fengwang_dir}/FENGWANG.md"


def memory_map_rel(config: ProjectConfig) -> str:
    if config.memory_root:
        return f"{config.memory_root}/memory-map.md"
    return f"{config.fengwang_dir}/memory-map.md"


# ---------------------------------------------------------------------------
# 诊断信封与退出码契约（附录 C）
# ---------------------------------------------------------------------------


@dataclass
class Diagnostic:
    severity: str  # error | warning | info
    code: str
    message: str
    target: str = ""
    fix: str = ""

    def to_dict(self) -> "dict[str, str]":
        data = {"severity": self.severity, "code": self.code, "message": self.message}
        # 可选键缺省时省略而非置 null（附录 C）
        if self.target:
            data["target"] = self.target
        if self.fix:
            data["fix"] = self.fix
        return data


def envelope_status(diagnostics: "list[Diagnostic]") -> str:
    if any(d.severity == "error" for d in diagnostics):
        return "error"
    if any(d.severity == "warning" for d in diagnostics):
        return "warn"
    return "ok"


def emit_envelope(
    command: str,
    diagnostics: "list[Diagnostic]",
    *,
    fmt: str = "text",
    payload: "dict | None" = None,
    ok_message: str = "",
    warn_mode: bool = False,
) -> int:
    """按附录 C 输出诊断并返回退出码。JSON 模式 stdout 恰好一份 JSON 文档。"""
    status = envelope_status(diagnostics)
    if fmt == "json":
        document = {"status": status, "command": command, "diagnostics": [d.to_dict() for d in diagnostics]}
        if payload:
            document.update(payload)
        print(json.dumps(document, ensure_ascii=False, indent=2))
    else:
        for diag in diagnostics:
            stream = sys.stderr if diag.severity == "error" else sys.stdout
            print(f"[{diag.severity}] {diag.code}: {diag.message}", file=stream)
            if diag.fix:
                print(f"  fix: {diag.fix}", file=stream)
        if status == "ok" and ok_message:
            print(ok_message)
    if warn_mode:
        return EXIT_OK
    return EXIT_FAILURE if status == "error" else EXIT_OK


# ---------------------------------------------------------------------------
# 记忆脚手架模板（内联模板是唯一事实源，D1；按 language 分派，D3）
# ---------------------------------------------------------------------------


def context_index_template(config: ProjectConfig, date: "str | None" = None) -> str:
    date = date or today()
    if is_en(config):
        return f"""# {config.project_name} Progressive Context Entry

> First entry point for AI sessions to understand project business context. Plain discussion, Plan mode, and read-only analysis never update this system; maintain it only after real development delivery.
> Last updated: {date}

## Project Positioning

To fill in: describe the business, users, and core flows this project serves in one sentence.

## Reading Path

1. A fresh session first reads `../FENGWANG.md` and `../memory-map.md` to route to the smallest necessary context.
2. Read this file to build the global business map.
3. Read `domains/domain-*.md` for the domain the request belongs to.
4. Read `impact-matrix.md` for cross-module impact.
5. For history, read `../{config.task_dir}/TASK-INDEX.md`, `../{config.plan_dir}/PLAN-INDEX.md`, `../{config.conversation_dir}/CONVERSATION-INDEX.md`, and `../{config.changelog_dir}/CHANGELOG-INDEX.md`.

## Domain Index

| Domain | Document | Status |
|--------|----------|--------|
| To identify | `domains/domain-general.md` | initialized |

## Key Business Flows

To fill in: describe main business flows with Mermaid or a short list.

## Maintenance Rules

- Real development completion must produce an immutable task record and changelog entry.
- Only stable, landed business facts may merge into `business-context/`.
- Every current business fact must trace back to a task record or changelog entry.
"""
    return f"""# {config.project_name} 渐进式上下文入口

> 本文件是 AI 理解项目业务上下文的第一入口。普通讨论、Plan 模式、只读分析不会更新本体系；只有实际开发交付后才维护。
> 最后更新：{date}

## 项目定位

待补充：用一句话描述本项目服务的业务、用户和核心流程。

## 阅读路径

1. 新会话先读取 `../FENGWANG.md` 和 `../memory-map.md`，按需求路由到最小必要上下文。
2. 再读本文件，建立项目全局业务地图。
3. 按需求所属领域读取 `domains/domain-*.md`。
4. 涉及跨模块影响时读取 `impact-matrix.md`。
5. 需要追溯历史时读取 `../{config.task_dir}/TASK-INDEX.md`、`../{config.plan_dir}/PLAN-INDEX.md`、`../{config.conversation_dir}/CONVERSATION-INDEX.md` 和 `../{config.changelog_dir}/CHANGELOG-INDEX.md`。

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


EMPTY_RULES_PLACEHOLDER_ZH = "（暂无现行规则条目。真实开发交付且业务规则变化后，由 `maintain --business-change` 按附录 B 格式写入。）"
EMPTY_RULES_PLACEHOLDER_EN = "(No active rule entries yet. `maintain --business-change` writes structured entries here after real delivery.)"
EMPTY_RETIRED_PLACEHOLDER_ZH = "（暂无）"
EMPTY_RETIRED_PLACEHOLDER_EN = "(None)"


def domain_template(config: ProjectConfig, domain: str = "general", date: "str | None" = None) -> str:
    date = date or today()
    if is_en(config):
        return f"""# {domain} Domain Context

> Last updated: {date}

## Domain Positioning

To fill in: what business problem this domain owns in {config.project_name}.

## Current Business Rules

{EMPTY_RULES_PLACEHOLDER_EN}

## Retired Rules

{EMPTY_RETIRED_PLACEHOLDER_EN}

## Core Entry Points

| Type | Path/API | Notes |
|------|----------|-------|
| To fill in | To fill in | To fill in |

## Upstream/Downstream

To fill in: what this domain depends on and impacts.
"""
    return f"""# {domain} 领域上下文

> 最后更新：{date}

## 领域定位

待补充：描述该领域在 {config.project_name} 中负责的业务问题。

## 当前业务规则

{EMPTY_RULES_PLACEHOLDER_ZH}

## 已废除规则

{EMPTY_RETIRED_PLACEHOLDER_ZH}

## 核心入口

| 类型 | 路径/接口 | 说明 |
|------|-----------|------|
| 待补充 | 待补充 | 待补充 |

## 上下游关系

待补充：记录该领域依赖谁、影响谁。
"""


EMPTY_FACTS_PLACEHOLDER_ZH = (
    "（暂无现行事实。用户在对话中用确凿语气断言项目事实后，"
    "由 `conversation --confirmed-fact` 写入，同名事实始终只有一条现行值。）"
)
EMPTY_FACTS_PLACEHOLDER_EN = (
    "(No active facts yet. `conversation --confirmed-fact` writes entries here after the user "
    "asserts a project fact; one fact name always keeps exactly one active value.)"
)


def project_facts_template(config: ProjectConfig, date: "str | None" = None) -> str:
    """项目事实登记表：入口、配置、术语锚点、代码约定等确凿事实的唯一现行值。"""
    date = date or today()
    if is_en(config):
        return f"""# Project Facts

> Confirmed project facts asserted by the user: entry points, config values, term anchors, code
> conventions. One fact name is a stable key — at most one active value at any moment.
> Anchors are clues, not guarantees: they are never re-verified against source code.
> Last updated: {date}

## Current Facts

{EMPTY_FACTS_PLACEHOLDER_EN}

## Retired Facts

{EMPTY_RETIRED_PLACEHOLDER_EN}
"""
    return f"""# 项目事实登记

> 记录用户在对话中确凿断言的项目事实：系统入口、关键配置、术语锚点、代码约定等。
> 一个事实名是稳定 key，同一时刻只有一条现行值；旧值移入「已失效事实」段。
> 注意：事实锚点是线索不是保证，本文件不与源码自动校验，接口改名或配置调整后需人工更新。
> 最后更新：{date}

## 现行事实

{EMPTY_FACTS_PLACEHOLDER_ZH}

## 已失效事实

{EMPTY_RETIRED_PLACEHOLDER_ZH}
"""


def impact_matrix_template(config: ProjectConfig) -> str:
    if is_en(config):
        return """# Change Impact Matrix

> Format: if you change X, check Y. Maintain incrementally with stable facts after real delivery.

| If changed | Check |
|------------|-------|
| To fill in | To fill in |
"""
    return """# 变更影响矩阵

> 格式：如果改 X，需要检查 Y。实际开发任务完成后按稳定事实增量维护。

| 如果变更 | 需要检查 |
|----------|----------|
| 待补充 | 待补充 |
"""


def debt_registry_template(config: ProjectConfig) -> str:
    if is_en(config):
        return """# Tech Debt & Known Pitfalls Registry

> Record only confirmed status, risk, and source. Never write guesses into current business truth.

| ID | Domain | Status | Risk | Source |
|----|--------|--------|------|--------|
| To fill in | To fill in | To fill in | To fill in | To fill in |
"""
    return """# 技术债务与历史坑点登记

> 只记录已确认的现状、风险和来源，不把讨论中的猜测写入当前业务真相。

| 编号 | 领域 | 现状 | 风险 | 来源 |
|------|------|------|------|------|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
"""


def task_index_template(config: ProjectConfig, date: "str | None" = None) -> str:
    date = date or today()
    if is_en(config):
        return f"""# Task Record Index

> Progressive entry for immutable task records: business intent, final approach, and evidence after real delivery.
> Last updated: {date}

## Recent Tasks

| Date | Domain | Task | Business Change | Record |
|------|--------|------|-----------------|--------|
"""
    return f"""# 任务记录索引

> 不可变任务记录的渐进式入口。记录实际开发交付后的业务意图、最终方案和实现证据。
> 最后更新：{date}

## 最近任务

| 日期 | 领域 | 任务 | 业务变化 | 记录 |
|------|------|------|----------|------|
"""


def changelog_index_template(config: ProjectConfig, date: "str | None" = None) -> str:
    date = date or today()
    if is_en(config):
        return f"""# Changelog Index

> Progressive changelog entry for locating history by time, domain, risk, API, and data changes.
> Last updated: {date}

## Recent Changes

| Date | Domain | Change | Type | Record |
|------|--------|--------|------|--------|

## By Domain

| Domain | Latest Record |
|--------|---------------|
"""
    return f"""# Changelog 索引

> changelog 的渐进式入口。用于按时间、领域、风险、接口和数据变化快速定位历史变更。
> 最后更新：{date}

## 最近变更

| 日期 | 领域 | 变更 | 类型 | 记录 |
|------|------|------|------|------|

## 按领域索引

| 领域 | 最近记录 |
|------|----------|
"""


def plan_index_template(config: ProjectConfig, date: "str | None" = None) -> str:
    date = date or today()
    if is_en(config):
        return f"""# Plan Record Index

> Progressive entry for plans and proposals. A plan is not landed business fact and must not be treated as current truth.
> Last updated: {date}

## Recent Plans

| Date | Domain | Status | Plan | Record |
|------|--------|--------|------|--------|
"""
    return f"""# Plan 记录索引

> 计划、方案和待实现设计的渐进式入口。Plan 不是已落地业务事实，不能直接当作当前业务真相。
> 最后更新：{date}

## 最近计划

| 日期 | 领域 | 状态 | 计划 | 记录 |
|------|------|------|------|------|
"""


def conversation_index_template(config: ProjectConfig, date: "str | None" = None) -> str:
    date = date or today()
    if is_en(config):
        return f"""# Conversation Memory Index

> Progressive entry for user business explanations, preferences, terms, boundaries, and rejected options. Summary-only by default.
> Last updated: {date}

## Recent Conversation Memory

| Date | Domain | Topic | Promote | Record |
|------|--------|-------|---------|--------|
"""
    return f"""# 对话上下文索引

> 用户业务解释、偏好、术语、边界和否定方案的渐进式入口。默认只保存萃取摘要，不保存完整对话。
> 最后更新：{date}

## 最近对话记忆

| 日期 | 领域 | 主题 | 建议提升 | 记录 |
|------|------|------|----------|------|
"""


def fengwang_template(config: ProjectConfig, date: "str | None" = None) -> str:
    date = date or today()
    if is_en(config):
        return f"""# FengWang Routing Entry

> Unified entry for a fresh AI session to understand {config.project_name}. Read this first, then route via `memory-map.md` to the smallest necessary context.
> Last updated: {date}

## Memory Layers

| Type | Directory | Semantics |
|------|-----------|-----------|
| Current truth | `{config.context_dir}/` | Current stable business truth |
| Landed tasks | `{config.task_dir}/` | Business intent, final approach, and evidence of delivered tasks |
| Change history | `{config.changelog_dir}/` | Landed code/config/database change history |
| Plans | `{config.plan_dir}/` | Plan-stage output, not landed fact |
| Conversation memory | `{config.conversation_dir}/` | User-explained background, preferences, terms, boundaries |

## New Request Flow

1. Read this file and `memory-map.md`.
2. Locate related records by business words, APIs, pages, tables, states, or permissions in the request.
3. Read the top 3 routed results first; read current truth before historical references.
4. On conflict: `business-context` is current truth; `task-records/changelog` is landed evidence; `plan-records/conversation-records` is historical reference.
5. Never read everything; prefer the 8-12 files FengWang routes to, within the output budget.

## Maintenance Rules

- After a final plan: maintain `{config.plan_dir}/` and `memory-map.md` only.
- After durable user business explanations: maintain `{config.conversation_dir}/` and `memory-map.md` only.
- After real development delivery: maintain `{config.task_dir}/`, `{config.changelog_dir}/`, update `{config.context_dir}/` for stable facts, and `memory-map.md`.
"""
    return f"""# FengWang 蜂王入口

> 本文件是新 AI 会话理解 {config.project_name} 的统一入口。先读本文件，再按 `memory-map.md` 路由到最小必要上下文。
> 最后更新：{date}

## 记忆分层

| 类型 | 目录 | 语义 |
|------|------|------|
| 当前事实 | `{config.context_dir}/` | 当前稳定业务真相 |
| 已落地任务 | `{config.task_dir}/` | 已交付开发任务的业务意图、最终方案和证据 |
| 变更历史 | `{config.changelog_dir}/` | 已落地代码、配置、数据库等变更历史 |
| 计划方案 | `{config.plan_dir}/` | Plan 模式或方案阶段产物，不代表已落地事实 |
| 对话记忆 | `{config.conversation_dir}/` | 用户解释过的业务背景、偏好、术语和边界 |

## 新需求处理流程

1. 读取本文件和 `memory-map.md`。
2. 根据用户需求中的业务词、接口、页面、数据表、状态或权限线索定位相关记录。
3. 路由结果先读前 3 条；优先读取当前事实，再读取相关对话、计划、任务和 changelog。
4. 如果记录冲突，以 `business-context` 为当前事实；`task-records/changelog` 为落地证据；`plan-records/conversation-records` 为历史参考。
5. 不全量读取所有记录，优先读取 FengWang 路由出的 8-12 个文件（输出有字节预算）。

## 维护规则

- Plan 产出后维护 `{config.plan_dir}/` 和 `memory-map.md`，不写 changelog，不写业务真相。
- 有长期价值的用户业务解释维护 `{config.conversation_dir}/` 和 `memory-map.md`。
- 真实开发完成后维护 `{config.task_dir}/`、`{config.changelog_dir}/`，必要时更新 `{config.context_dir}/` 和 `memory-map.md`。
"""


def memory_map_template(config: ProjectConfig, date: "str | None" = None) -> str:
    date = date or today()
    if is_en(config):
        return f"""# FengWang Memory Map

> Progressive routing table by domain, keywords, APIs, files, states, and business flows.
> Last updated: {date}

| Type | Status | Domain | Keywords | Read First | Notes |
|------|--------|--------|----------|------------|-------|
| context | current | general | project context business current truth | [CONTEXT-INDEX.md]({config.context_dir}/CONTEXT-INDEX.md) | Current business context entry |
| fact | current | general | fact entry point api config term convention constant | [{PROJECT_FACTS_FILE}]({config.context_dir}/{PROJECT_FACTS_FILE}) | User-confirmed project facts |
| task | historical | general | task development landed implementation | [TASK-INDEX.md]({config.task_dir}/TASK-INDEX.md) | Landed task entry |
| changelog | historical | general | changelog change history code | [CHANGELOG-INDEX.md]({config.changelog_dir}/CHANGELOG-INDEX.md) | Change history entry |
| plan | proposed | general | plan proposal design | [PLAN-INDEX.md]({config.plan_dir}/PLAN-INDEX.md) | Plan record entry |
| conversation | historical | general | conversation explanation term preference boundary | [CONVERSATION-INDEX.md]({config.conversation_dir}/CONVERSATION-INDEX.md) | Conversation memory entry |
"""
    return f"""# FengWang Memory Map

> 按领域、关键词、接口、文件、状态和业务链路维护的渐进式路由表。
> 最后更新：{date}

| 类型 | 状态 | 领域 | 触发词/线索 | 优先读取 | 说明 |
|------|------|------|-------------|----------|------|
| context | current | general | 项目 上下文 业务 当前事实 | [CONTEXT-INDEX.md]({config.context_dir}/CONTEXT-INDEX.md) | 当前业务上下文入口 |
| fact | current | general | 事实 入口 接口 配置 术语 约定 常量 | [{PROJECT_FACTS_FILE}]({config.context_dir}/{PROJECT_FACTS_FILE}) | 用户确认的项目事实登记 |
| task | historical | general | 任务 开发 落地 实现 | [TASK-INDEX.md]({config.task_dir}/TASK-INDEX.md) | 已落地任务入口 |
| changelog | historical | general | changelog 变更 历史 代码 | [CHANGELOG-INDEX.md]({config.changelog_dir}/CHANGELOG-INDEX.md) | 变更历史入口 |
| plan | proposed | general | plan 计划 方案 设计 | [PLAN-INDEX.md]({config.plan_dir}/PLAN-INDEX.md) | 计划记录入口 |
| conversation | historical | general | 对话 解释 术语 偏好 边界 | [CONVERSATION-INDEX.md]({config.conversation_dir}/CONVERSATION-INDEX.md) | 对话记忆入口 |
"""


# ---------------------------------------------------------------------------
# 宿主注入产物：marker 块、薄入口、薄命令（A3 / A4）
# ---------------------------------------------------------------------------


def host_snippet(config: ProjectConfig) -> str:
    """写入 CLAUDE.md / AGENTS.md 的 marker 块内容，必须保持简短（≤15 行）。"""
    entry = fengwang_entry_rel(config)
    mmap = memory_map_rel(config)
    if is_en(config):
        return f"""## FengChaoSkills Business Memory

- New session: read `{entry}` first and route the smallest context via `{mmap}`.
- Trigger boundary: maintain memory only after real development delivery; discussion, Plan mode, and read-only analysis never write task-records/changelog.
- After delivery run `python3 {CLI_RELATIVE} maintain ...`; full rules live in `{SKILL_INSTALL_DIR}/SKILL.md` — read and follow it."""
    return f"""## FengChaoSkills 业务记忆

- 新会话先读 `{entry}`，按 `{mmap}` 路由最小必要上下文。
- 触发边界：仅真实开发交付后维护记忆；讨论、Plan 模式、只读分析不写 task-records/changelog。
- 交付后执行 `python3 {CLI_RELATIVE} maintain ...`；完整规则见 `{SKILL_INSTALL_DIR}/SKILL.md`，读取并遵循。"""


def marker_block(inner: str) -> str:
    return f"{MARKER_START}\n{inner.strip()}\n{MARKER_END}\n"


def inject_marker_block(path: Path, inner: str) -> bool:
    """向宿主文件注入/更新 marker 块；用户原内容一字不动（A3）。"""
    block = marker_block(inner)
    existing = read_text(path)
    if MARKER_START in existing and MARKER_END in existing:
        pattern = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"\n?", re.DOTALL)
        updated = pattern.sub(block, existing, count=1)
        if updated == existing:
            return False
        write_text(path, updated)
        return True
    if existing:
        write_text(path, existing.rstrip("\n") + "\n\n" + block)
    else:
        write_text(path, block)
    return True


def remove_marker_block(path: Path) -> bool:
    """摘除 marker 块；文件仅剩空白时删除文件（卸载对称性，红线 6）。"""
    existing = read_text(path)
    if MARKER_START not in existing:
        return False
    marker_block_pattern = re.compile(
        r"\n*" + re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"\n?", re.DOTALL
    )
    updated = marker_block_pattern.sub("", existing, count=1)
    if updated.strip() == "":
        path.unlink()
        return True
    if not updated.endswith("\n"):
        updated += "\n"
    write_text(path, updated)
    return True


def thin_skill_entry(config: ProjectConfig) -> str:
    """各 agent skills 目录下的薄入口：只指向 .fengchao/skill/，不复制正文。"""
    if is_en(config):
        body = (
            "This file is a thin entry only. Read `"
            + SKILL_INSTALL_DIR
            + "/SKILL.md` and follow it.\n"
            + f"The engine command is `python3 {CLI_RELATIVE}`.\n"
        )
    else:
        body = (
            "本文件只是薄入口。请读取并遵循 `"
            + SKILL_INSTALL_DIR
            + "/SKILL.md`。\n"
            + f"引擎命令为 `python3 {CLI_RELATIVE}`。\n"
        )
    return f"""---
name: fengchao-business-memory
description: Route project business memory and maintain it after real development delivery. Read {SKILL_INSTALL_DIR}/SKILL.md and follow it.
---

# FengChao Business Memory (thin entry)

{body}"""


def cursor_rule(config: ProjectConfig) -> str:
    entry = fengwang_entry_rel(config)
    if is_en(config):
        return f"""---
description: FengChao business memory trigger rules (thin entry). Maintain memory only after real development delivery.
globs:
alwaysApply: true
---

# FengChaoSkills

New session: read `{entry}` first and route the smallest necessary context via `{memory_map_rel(config)}`.

Trigger boundary: only real development delivery maintains memory; discussion, Plan mode, and read-only analysis never write task-records/changelog.

Full rules: read `{SKILL_INSTALL_DIR}/SKILL.md` and follow it. Engine command: `python3 {CLI_RELATIVE}`.
"""
    return f"""---
description: 实际开发交付后维护 FengChao 业务记忆；讨论、Plan、只读分析不触发（薄入口）。
globs:
alwaysApply: true
---

# FengChaoSkills

新会话先读 `{entry}`，按 `{memory_map_rel(config)}` 路由到最小必要上下文。

触发边界：仅真实开发交付后维护记忆；讨论、Plan 模式、只读分析不写 task-records/changelog。

完整规则读取 `{SKILL_INSTALL_DIR}/SKILL.md` 并遵循。引擎命令：`python3 {CLI_RELATIVE}`。
"""


def command_file_content(config: ProjectConfig, agent: str, verb: str) -> str:
    """薄命令文件（A4）：≤10 行，逻辑全在 CLI 引擎。Cursor 无 frontmatter。"""
    en = is_en(config)
    bodies_zh = {
        "route": (
            f"运行 `python3 {CLI_RELATIVE} fengwang --query \"$ARGUMENTS\"`。\n"
            "读取返回的前 3 条记录文件，向用户汇报相关业务记忆要点与出处。\n"
            f"遵循 `{SKILL_INSTALL_DIR}/SKILL.md`。\n"
        ),
        "remember": (
            "按 conversation capture 模式从当前对话萃取用户业务解释（背景、术语、偏好、否定项）。\n"
            f"执行 `python3 {CLI_RELATIVE} conversation --title \"...\" --summary \"...\"`（按需加 --term/--preference/--rejected）。\n"
            f"只保存萃取摘要，不保存完整对话；遵循 `{SKILL_INSTALL_DIR}/SKILL.md`。\n"
        ),
        "status": (
            f"运行 `python3 {CLI_RELATIVE} status`，向用户解读输出：启用状态、各层记录数、最近记录、健康度。\n"
        ),
    }
    bodies_en = {
        "route": (
            f"Run `python3 {CLI_RELATIVE} fengwang --query \"$ARGUMENTS\"`.\n"
            "Read the top 3 returned record files and report the relevant business memory with sources.\n"
            f"Follow `{SKILL_INSTALL_DIR}/SKILL.md`.\n"
        ),
        "remember": (
            "Extract the user's business explanation (background, terms, preferences, rejected options) from this conversation.\n"
            f"Run `python3 {CLI_RELATIVE} conversation --title \"...\" --summary \"...\"` (add --term/--preference/--rejected as needed).\n"
            f"Store extracted summary only; follow `{SKILL_INSTALL_DIR}/SKILL.md`.\n"
        ),
        "status": (
            f"Run `python3 {CLI_RELATIVE} status` and interpret the output for the user: enabled state, record counts, latest record, health.\n"
        ),
    }
    descriptions = {
        "route": "FengChao：按查询找回相关业务记忆" if not en else "FengChao: route back relevant business memory",
        "remember": "FengChao：把刚才的业务解释记入记忆" if not en else "FengChao: capture the explanation into memory",
        "status": "FengChao：查看业务记忆系统状态" if not en else "FengChao: show business memory status",
    }
    body = (bodies_en if en else bodies_zh)[verb]
    if agent == "cursor":
        # Cursor 命令为纯 Markdown、无 frontmatter；$ARGUMENTS 替换为文字说明
        plain = body.replace('"$ARGUMENTS"', ("\"<user query>\"" if en else "\"<用户输入的查询词>\""))
        return f"# {descriptions[verb]}\n\n{plain}"
    return f"""---
description: {descriptions[verb]}
---

{body}"""


def opencode_config(config: ProjectConfig) -> str:
    entry = fengwang_entry_rel(config)
    mmap = memory_map_rel(config)
    context_glob = (
        f"{config.memory_root}/{config.context_dir}/**/*.md"
        if config.memory_root
        else f"{config.context_dir}/**/*.md"
    )
    return json.dumps(
        {
            "$schema": "https://opencode.ai/config.json",
            "instructions": ["AGENTS.md", entry, mmap, context_glob],
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


# ---------------------------------------------------------------------------
# 宿主注入的安装与对称摘除（A2 / A3 / 红线 6）
# ---------------------------------------------------------------------------

THIN_SKILL_PATHS = {
    "claude": ".claude/skills/fengchao-business-memory/SKILL.md",
    "opencode": ".opencode/skills/fengchao-business-memory/SKILL.md",
    "codex": ".codex/skills/fengchao-business-memory/SKILL.md",
    "agents": ".agents/skills/fengchao-business-memory/SKILL.md",
}
CURSOR_RULE_PATH = ".cursor/rules/fengchao.mdc"
MARKER_HOSTS = {
    "claude": "CLAUDE.md",
    "codex": "AGENTS.md",
    "opencode": "AGENTS.md",
    "agents": "AGENTS.md",
}
# hook 以会话 cwd 运行，cwd 可能在项目子目录：用 $CLAUDE_PROJECT_DIR 锚定项目根，
# 变量缺失时回退 "."（等价旧行为）。双引号保证路径含空格时不炸（F-005）。
HOOK_COMMAND_PREFIX = f'python3 "${{CLAUDE_PROJECT_DIR:-.}}/{CLI_RELATIVE}" hook '
# 维护规则：HOOK_COMMAND_PREFIX 每次变更，旧值必须追加进 LEGACY_HOOK_COMMAND_PREFIXES
# 且永不删除条目——remove_claude_hooks 必须能摘除任何历史版本写入的 hook（红线 6 卸载对称性）。
LEGACY_HOOK_COMMAND_PREFIXES = (
    f"python3 {CLI_RELATIVE} hook ",  # <= v0.2.0：裸相对路径，cwd 在子目录时失效（F-005）
)
ALL_HOOK_COMMAND_PREFIXES = (HOOK_COMMAND_PREFIX,) + LEGACY_HOOK_COMMAND_PREFIXES


def agent_artifact_files(config: ProjectConfig, agent: str) -> "dict[str, str]":
    """某个 agent surface 需要写入的薄文件（路径 → 内容），全部可对称删除。"""
    files: "dict[str, str]" = {}
    if agent in THIN_SKILL_PATHS:
        files[THIN_SKILL_PATHS[agent]] = thin_skill_entry(config)
    if agent == "cursor":
        files[CURSOR_RULE_PATH] = cursor_rule(config)
    if agent in AGENT_COMMAND_PATHS:
        for verb in COMMAND_VERBS:
            files[AGENT_COMMAND_PATHS[agent].format(verb=verb)] = command_file_content(config, agent, verb)
    return files


def all_agent_artifact_paths() -> "list[str]":
    """全部 agent 可能写入的薄文件路径（用于 disable/uninstall 的彻底摘除）。"""
    paths = list(THIN_SKILL_PATHS.values()) + [CURSOR_RULE_PATH]
    for agent, pattern in AGENT_COMMAND_PATHS.items():
        for verb in COMMAND_VERBS:
            paths.append(pattern.format(verb=verb))
    return paths


def filter_fengchao_hooks(
    entries: "list[dict]", keep_command: "str | None" = None
) -> "tuple[list[dict], bool]":
    """从 hook entries 中剥除本工具写入的条目（含全部历史格式）。

    keep_command 非空时，与其精确相等的命令保留（register 幂等场景）。
    返回 (保留的 entries, 是否有改动)。用户自有 hook 一律原样保留。
    """
    changed = False
    kept_entries: "list[dict]" = []
    for entry in entries:
        entry_hooks = []
        for hook in entry.get("hooks", []):
            command = str(hook.get("command", ""))
            ours = any(prefix in command for prefix in ALL_HOOK_COMMAND_PREFIXES)
            if ours and command != keep_command:
                changed = True
                continue
            entry_hooks.append(hook)
        if entry_hooks:
            if len(entry_hooks) != len(entry.get("hooks", [])):
                entry = dict(entry)
                entry["hooks"] = entry_hooks
            kept_entries.append(entry)
        elif entry.get("hooks"):
            # 整条 entry 都是我们的 hook，摘除
            changed = True
        else:
            kept_entries.append(entry)
    return kept_entries, changed


def register_claude_hooks(project: Path) -> bool:
    """向 .claude/settings.json 注册 SessionStart / Stop hooks（B1）。"""
    settings_path = project / ".claude" / "settings.json"
    raw = read_text(settings_path)
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        print(f"warning: {settings_path} 不是合法 JSON，跳过 hook 注册", file=sys.stderr)
        return False
    hooks = data.setdefault("hooks", {})
    changed = False
    for event, sub in (("SessionStart", "session-start"), ("Stop", "stop-gate")):
        command = HOOK_COMMAND_PREFIX + sub
        # 先剥除历史格式条目：升级路径是"替换"而非"追加"（避免新旧 hook 并存重复触发）
        entries, stripped = filter_fengchao_hooks(hooks.setdefault(event, []), keep_command=command)
        hooks[event] = entries
        changed = changed or stripped
        already = any(
            hook.get("command") == command
            for entry in entries
            for hook in entry.get("hooks", [])
        )
        if not already:
            entries.append({"hooks": [{"type": "command", "command": command, "timeout": 10}]})
            changed = True
    if changed:
        write_text(settings_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return changed


def remove_claude_hooks(project: Path) -> bool:
    settings_path = project / ".claude" / "settings.json"
    raw = read_text(settings_path)
    if not raw.strip():
        return False
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False
    changed = False
    for event in list(hooks.keys()):
        entries = hooks.get(event) or []
        kept_entries, event_changed = filter_fengchao_hooks(entries)
        changed = changed or event_changed
        if kept_entries:
            hooks[event] = kept_entries
        else:
            hooks.pop(event, None)
    if not hooks:
        data.pop("hooks", None)
    if not changed:
        return False
    if not data:
        settings_path.unlink()
    else:
        write_text(settings_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return True


def install_host_injections(
    project: Path, config: ProjectConfig, *, notes: "list[str]"
) -> "list[str]":
    """按 config.agents 安装薄文件、marker 块、opencode.json 与 hooks。返回写入路径。"""
    written: "list[str]" = []
    marker_targets: "list[str]" = []
    for agent in config.agents:
        for rel, content in agent_artifact_files(config, agent).items():
            path = project / rel
            if read_text(path) != content:
                write_text(path, content)
                written.append(rel)
        host = MARKER_HOSTS.get(agent)
        if host and host not in marker_targets:
            marker_targets.append(host)
    for host in marker_targets:
        if inject_marker_block(project / host, host_snippet(config)):
            written.append(host)
    if "opencode" in config.agents:
        opencode_path = project / "opencode.json"
        content = opencode_config(config)
        if not opencode_path.exists():
            write_text(opencode_path, content)
            written.append("opencode.json")
        elif read_text(opencode_path) != content:
            # JSON 无注释语法，无法安全 marker 化：不动用户文件，打印手工合并指引（A3）
            notes.append(
                "opencode.json 已存在，未修改。如需接入请手工把以下 instructions 合并进去："
                + " ".join(json.loads(content)["instructions"])
            )
    if "claude" in config.agents and config.with_hooks:
        if register_claude_hooks(project):
            written.append(".claude/settings.json")
    return written


def remove_host_injections(project: Path, config: ProjectConfig) -> "list[str]":
    """disable/uninstall 的对称摘除：装了什么就摘什么，不碰用户内容。"""
    removed: "list[str]" = []
    for rel in all_agent_artifact_paths():
        path = project / rel
        if path.exists():
            path.unlink()
            removed.append(rel)
            # 清理因此变空的目录（只 rmdir 空目录，安全）
            parent = path.parent
            while parent != project:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
    for host in ("CLAUDE.md", "AGENTS.md"):
        if remove_marker_block(project / host):
            removed.append(host)
    opencode_path = project / "opencode.json"
    if opencode_path.exists() and read_text(opencode_path) == opencode_config(config):
        opencode_path.unlink()
        removed.append("opencode.json")
    if remove_claude_hooks(project):
        removed.append(".claude/settings.json")
    return removed


# ---------------------------------------------------------------------------
# init 与 skill 安装（A1）
# ---------------------------------------------------------------------------


def skill_source_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def install_project_skill(project: Path) -> str:
    """把 skill 完整复制到唯一安装点 .fengchao/skill/（单副本，A1）。"""
    source = skill_source_dir()
    target = project / SKILL_INSTALL_DIR
    if not (source / "SKILL.md").exists():
        raise FileNotFoundError(
            f"skill source not found at {source}; run from a full FengChaoSkills checkout or package"
        )
    if target.exists():
        shutil.rmtree(target)
    ensure_dir(target.parent)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "__init__.py"),
    )
    return SKILL_INSTALL_DIR


def detect_agents(project: Path) -> "tuple[str, ...]":
    detected: "list[str]" = []
    surface_markers = {
        "claude": project / ".claude",
        "cursor": project / ".cursor",
        "codex": project / ".codex",
        "opencode": project / ".opencode",
        "agents": project / "AGENTS.md",
    }
    for agent, marker in surface_markers.items():
        if marker.exists():
            detected.append(agent)
    return tuple(detected)


def determine_agents(project: Path, args: argparse.Namespace) -> "tuple[str, ...]":
    if args.agents:
        requested = tuple(a.strip() for a in args.agents.split(",") if a.strip())
        invalid = [a for a in requested if a not in AGENT_CHOICES]
        if invalid:
            raise SystemExit(f"unknown agents: {', '.join(invalid)} (choices: {', '.join(AGENT_CHOICES)})")
        return requested
    detected = detect_agents(project)
    if detected:
        return detected
    if sys.stdin.isatty() and sys.stdout.isatty():
        answer = input(f"选择要接入的 agent（逗号分隔，可选 {','.join(AGENT_CHOICES)}，回车=全部）: ").strip()
        if answer:
            return tuple(a.strip() for a in answer.split(",") if a.strip() in AGENT_CHOICES)
    # 非 TTY 环境默认全装薄入口（A1）
    return AGENT_CHOICES


def memory_scaffold_files(config: ProjectConfig, layout: Layout) -> "dict[Path, str]":
    return {
        layout.fengwang_dir / "FENGWANG.md": fengwang_template(config),
        layout.fengwang_dir / "memory-map.md": memory_map_template(config),
        layout.context_dir / "CONTEXT-INDEX.md": context_index_template(config),
        layout.context_dir / "domains" / "domain-general.md": domain_template(config),
        layout.context_dir / PROJECT_FACTS_FILE: project_facts_template(config),
        layout.context_dir / "impact-matrix.md": impact_matrix_template(config),
        layout.context_dir / "debt-registry.md": debt_registry_template(config),
        layout.task_dir / "TASK-INDEX.md": task_index_template(config),
        layout.changelog_dir / "CHANGELOG-INDEX.md": changelog_index_template(config),
        layout.plan_dir / "PLAN-INDEX.md": plan_index_template(config),
        layout.conversation_dir / "CONVERSATION-INDEX.md": conversation_index_template(config),
    }


def init_project(project: Path, args: argparse.Namespace) -> int:
    agents: "tuple[str, ...]" = ()
    if not args.memory_only:
        agents = determine_agents(project, args)
    config = ProjectConfig(
        project_name=args.project_name or project.name,
        memory_root=args.memory_root,
        language=args.language,
        enabled=True,
        agents=agents,
        hook_mode=args.hook_mode,
        with_hooks=not args.no_hooks,
        installed_version=__version__,
    )
    layout = resolve_layout(project, config)

    created: "list[str]" = []
    notes: "list[str]" = []

    save_config(project, config)
    created.append(".fengchao/config.yaml")
    if write_if_missing(project / ".fengchao" / ".gitignore", "tmp/\n"):
        created.append(".fengchao/.gitignore")

    for path, content in memory_scaffold_files(config, layout).items():
        if write_if_missing(path, content):
            created.append(str(path.relative_to(project)))

    if not args.memory_only:
        created.append(install_project_skill(project))
        created.extend(install_host_injections(project, config, notes=notes))

    print("FengChao initialized")
    print(f"memory root: {config.memory_root or '(legacy root)'}  language: {config.language}")
    if agents:
        print(f"agents: {', '.join(agents)}" + ("  hooks: on" if config.with_hooks and "claude" in agents else ""))
    for path in created:
        print(f"created {path}")
    for note in notes:
        print(f"note: {note}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# 生命周期命令：enable / disable / uninstall / status（A2）
# ---------------------------------------------------------------------------


def require_config(project: Path) -> "ProjectConfig | None":
    if not (project / ".fengchao" / "config.yaml").exists():
        print("未找到 .fengchao/config.yaml，请先运行 init", file=sys.stderr)
        return None
    return load_config(project)


def disable_project(project: Path, args: argparse.Namespace) -> int:
    config = require_config(project)
    if config is None:
        return EXIT_FAILURE
    removed = remove_host_injections(project, config)
    save_config(project, replace(config, enabled=False))
    print("FengChao disabled（记忆数据与 .fengchao/ 全部保留）")
    for path in removed:
        print(f"removed {path}")
    return EXIT_OK


def enable_project(project: Path, args: argparse.Namespace) -> int:
    config = require_config(project)
    if config is None:
        return EXIT_FAILURE
    config = replace(config, enabled=True)
    notes: "list[str]" = []
    written = install_host_injections(project, config, notes=notes)
    save_config(project, config)
    print("FengChao enabled")
    for path in written:
        print(f"written {path}")
    for note in notes:
        print(f"note: {note}")
    return EXIT_OK


def uninstall_project(project: Path, args: argparse.Namespace) -> int:
    config = require_config(project)
    if config is None:
        return EXIT_FAILURE
    layout = resolve_layout(project, config)
    removed = remove_host_injections(project, config)
    fengchao_dir = project / ".fengchao"
    if fengchao_dir.exists():
        shutil.rmtree(fengchao_dir)
        removed.append(".fengchao/")
    print("FengChao uninstalled")
    for path in removed:
        print(f"removed {path}")
    memory_display = config.memory_root or "（项目根下的六个记忆目录）"
    if args.purge_memory:
        # 红线 5：删除记忆数据必须显式二次确认
        if not args.yes:
            if not sys.stdin.isatty():
                print("拒绝删除记忆数据：--purge-memory 需要交互式确认或显式 --yes", file=sys.stderr)
                return EXIT_CANCELLED
            answer = input(f"确认永久删除记忆数据 {memory_display} ？输入 yes 确认: ").strip().lower()
            if answer != "yes":
                print("已取消，记忆数据保留")
                return EXIT_CANCELLED
        for directory in {layout.memory_root} if not layout.is_legacy else set(layout.memory_dirs()):
            if directory.exists() and directory != project:
                shutil.rmtree(directory)
                print(f"purged {directory.relative_to(project)}")
        return EXIT_OK
    print(f"记忆数据已保留：{memory_display}（属于你的项目文档，可继续入 git）")
    return EXIT_OK


def count_records(directory: Path) -> "tuple[int, int, str]":
    """返回 (现役记录数, 归档记录数, 最近日期)。"""
    if not directory.exists():
        return 0, 0, ""
    active = [p for p in directory.glob("*.md") if RECORD_FILE_RE.match(p.name)]
    archived = [p for p in (directory / "archive").glob("*.md") if RECORD_FILE_RE.match(p.name)] if (directory / "archive").exists() else []
    latest = ""
    for p in active + archived:
        match = RECORD_FILE_RE.match(p.name)
        if match and match.group(1) > latest:
            latest = match.group(1)
    return len(active), len(archived), latest


def status_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    layout = resolve_layout(project, config)
    diagnostics: "list[Diagnostic]" = []
    initialized = (project / ".fengchao" / "config.yaml").exists() or layout.fengwang_dir.joinpath("FENGWANG.md").exists()

    if layout.is_legacy and initialized:
        diagnostics.append(
            Diagnostic(
                severity="info",
                code="legacy_layout",
                message="检测到老布局（六个记忆目录散在项目根下）",
                fix="运行 `fengchao.py migrate` 迁移到单一记忆根布局",
            )
        )
    if config.installed_version and config.installed_version != __version__:
        diagnostics.append(
            Diagnostic(
                severity="info",
                code="version_drift",
                message=f"项目内安装版本 {config.installed_version} 落后于当前 CLI {__version__}",
                fix="运行 `fengchao.py upgrade` 重写工具本体（不动记忆数据）",
            )
        )

    counts = {}
    latest_overall = ""
    for name, directory in layout.record_dirs():
        active, archived, latest = count_records(directory)
        counts[name] = {"active": active, "archived": archived}
        if latest > latest_overall:
            latest_overall = latest

    check_errors = collect_check_diagnostics(project, config, layout, require_records=False)
    health = "ok" if not any(d.severity == "error" for d in check_errors) else "fail"

    payload = {
        "version": __version__,
        "installed_version": config.installed_version,
        "enabled": config.enabled,
        "initialized": initialized,
        "layout": "legacy" if layout.is_legacy else "single-root",
        "memory_root": config.memory_root,
        "language": config.language,
        "agents": list(config.agents),
        "hook_mode": config.hook_mode,
        "records": counts,
        "latest_record": latest_overall,
        "check": health,
    }
    if args.format == "json":
        return emit_envelope("status", diagnostics, fmt="json", payload=payload, warn_mode=True)
    print("FengChao status")
    print(f"- version: {__version__}" + (f" (installed: {config.installed_version})" if config.installed_version else ""))
    print(f"- initialized: {'yes' if initialized else 'no'}")
    print(f"- enabled: {'yes' if config.enabled else 'no'}")
    print(f"- layout: {payload['layout']}" + (f" (memory root: {config.memory_root})" if config.memory_root else ""))
    print(f"- language: {config.language}")
    print(f"- agents: {', '.join(config.agents) or '(none)'}  hook_mode: {config.hook_mode}")
    record_summary = "  ".join(
        f"{name}={info['active']}" + (f"(+{info['archived']} archived)" if info["archived"] else "")
        for name, info in counts.items()
    )
    print(f"- records: {record_summary}")
    print(f"- latest record: {latest_overall or '(none)'}")
    print(f"- check: {health}")
    for diag in diagnostics:
        print(f"[{diag.severity}] {diag.code}: {diag.message}")
        if diag.fix:
            print(f"  fix: {diag.fix}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# 记录内容模板（task / changelog / plan / conversation）
# ---------------------------------------------------------------------------


def next_record_path(directory: Path, title: str) -> Path:
    date = today()
    existing = sorted(directory.glob(f"{date}_*.md"))
    seq = len(existing) + 1
    return directory / f"{date}_{seq:03d}_{slugify(title)}.md"


def optional_list(values: "list[str] | None") -> "list[str]":
    return [value for value in (values or []) if value.strip()]


def bullet_list(items: "list[str]") -> str:
    return "\n".join(f"- {item}" for item in items)


def normalize_memory_relative(
    paths: "list[str] | None",
    config: ProjectConfig,
    default_dir: str = "",
) -> "list[str]":
    """把 --from-plan/--from-conversation 的来源写法归一为记忆根相对完整路径。

    接受三种写法：裸记录名、记忆根相对路径、项目根相对路径。依次剥离记忆根前缀、
    补默认目录段（值内不含 `/` 时）、补 `.md` 后缀，保证 task-record 里生成的相对
    链接可解析（F-006：裸记录名曾产出 `../<名字>` 断链，check 报 broken_link）。
    以 `../` 开头的视为调用方显式指定的记忆根外引用，原样保留（同 F-003 边界纪律）。
    """
    prefix = config.memory_root + "/" if config.memory_root else ""
    normalized: "list[str]" = []
    for item in optional_list(paths):
        item = item.strip()
        if prefix and item.startswith(prefix):
            item = item[len(prefix):]
        if not item.startswith("../"):
            if default_dir and "/" not in item:
                item = f"{default_dir}/{item}"
            if not item.endswith(".md"):
                item = f"{item}.md"
        normalized.append(item)
    return normalized


def project_relative_link_list(paths: "list[str] | None", none_label: str = "- 无") -> str:
    items = optional_list(paths)
    if not items:
        return none_label
    rows: "list[str]" = []
    for item in items:
        target = item if item.startswith("../") else f"../{item}"
        rows.append(f"- [{item}]({target})")
    return "\n".join(rows)


def task_record_content(
    config: ProjectConfig,
    args: argparse.Namespace,
    changelog_name: str,
    timestamp: "str | None" = None,
) -> str:
    timestamp = timestamp or now_minutes()
    changed_files = optional_list(args.changed_file)
    evidence = optional_list(args.evidence)
    validation = optional_list(args.validation)
    tier = "full" if args.business_change else "lite"
    en = is_en(config)
    rule_line = ""
    if args.business_change:
        if en:
            rule_line = f"\n- **Rule name**：{args.rule_name}（change-kind：{args.change_kind}）"
        else:
            rule_line = f"\n- **规则名**：{args.rule_name}（change-kind：{args.change_kind}）"
    if en:
        return f"""# {args.title}

- **Recorded**：{timestamp}
- **Domain**：{args.domain}
- **Tier**：{tier}{rule_line}
- **Privacy**：extracted summary only, never the full conversation
- **Changelog**：`../{config.changelog_dir}/{changelog_name}`
- **From plan**：
{project_relative_link_list(args.from_plan, "- none")}
- **From conversation**：
{project_relative_link_list(args.from_conversation, "- none")}

## Real Business Need

{args.summary}

## Confirmed Business Rule

{args.business_change or "No stable business rule change this time."}

## Final Implementation

{args.implementation}

## Key Decisions & Trade-offs

{args.decision or "No extra trade-offs recorded."}

## Scope

| Type | Content |
|------|---------|
| Domain | `{args.domain}` |
| Files | {", ".join(f"`{item}`" for item in changed_files) if changed_files else "not recorded"} |

## Evidence

{bullet_list(evidence) if evidence else "- not recorded"}

## Validation

{bullet_list(validation) if validation else "- not recorded"}

## Follow-up Risks

{args.risk or "None."}
"""
    return f"""# {args.title}

- **记录时间**：{timestamp}
- **领域**：{args.domain}
- **交付档位**：{tier}{rule_line}
- **隐私策略**：只保存对话萃取摘要，不保存完整对话
- **关联 changelog**：`../{config.changelog_dir}/{changelog_name}`
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


def changelog_content(
    config: ProjectConfig,
    args: argparse.Namespace,
    task_name: str,
    timestamp: "str | None" = None,
) -> str:
    timestamp = timestamp or now_minutes()
    changed_files = optional_list(args.changed_file)
    en = is_en(config)
    if en:
        task_ref = f"`../{config.task_dir}/{task_name}`" if task_name else "none (lite delivery, no task record)"
        return f"""# {args.title}

- **Changed at**：{timestamp}
- **Domain**：{args.domain}
- **Change type**：{args.change_type}
- **Task record**：{task_ref}

## Summary

{args.summary}

## Business Change

{args.business_change or "No stable business rule change this time."}

## Implementation Notes

{args.implementation}

## Files

{bullet_list(changed_files) if changed_files else "- not recorded"}

## Validation

{bullet_list(optional_list(args.validation)) if args.validation else "- not recorded"}
"""
    task_ref = f"`../{config.task_dir}/{task_name}`" if task_name else "无（lite 交付，未生成 task-record）"
    return f"""# {args.title}

- **变更时间**：{timestamp}
- **领域**：{args.domain}
- **变更类型**：{args.change_type}
- **关联任务记录**：{task_ref}

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


def plan_record_content(config: ProjectConfig, args: argparse.Namespace, timestamp: "str | None" = None) -> str:
    timestamp = timestamp or now_minutes()
    assumptions = optional_list(args.assumption)
    open_questions = optional_list(args.open_question)
    impact = optional_list(args.impact)
    if is_en(config):
        return f"""# {args.title}

- **Recorded**：{timestamp}
- **Domain**：{args.domain}
- **Plan status**：{args.status}
- **Capture policy**：final-plan-only

## User Goal

{args.goal}

## Business Context As Understood

{args.context or "Not recorded."}

## The Plan

{args.plan}

## Key Assumptions

{bullet_list(assumptions) if assumptions else "- none"}

## Open Questions

{bullet_list(open_questions) if open_questions else "- none"}

## Expected Impact

{bullet_list(impact) if impact else "- not recorded"}

## Landing Links

- task-records：to fill in after landing
- changelog：to fill in after landing
"""
    return f"""# {args.title}

- **记录时间**：{timestamp}
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


def conversation_record_content(config: ProjectConfig, args: argparse.Namespace, timestamp: "str | None" = None) -> str:
    timestamp = timestamp or now_minutes()
    terms = optional_list(args.term)
    preferences = optional_list(args.preference)
    rejected = optional_list(args.rejected)
    unverified = optional_list(args.unverified)
    related = optional_list(args.related)
    if is_en(config):
        return f"""# {args.title}

- **Recorded**：{timestamp}
- **Domain**：{args.domain}
- **Privacy**：extracted summary only, never the full conversation
- **Promote to business-context**：{args.promote}

## Business Background Explained by the User

{args.summary}

## Terms & Meanings

{bullet_list(terms) if terms else "- not recorded"}

## Preferences & Constraints

{bullet_list(preferences) if preferences else "- not recorded"}

## Explicitly Rejected Options

{bullet_list(rejected) if rejected else "- not recorded"}

## Unverified / Not Landed

{bullet_list(unverified) if unverified else "- not recorded"}

## Related Records

{bullet_list(related) if related else "- none"}
"""
    return f"""# {args.title}

- **记录时间**：{timestamp}
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


# ---------------------------------------------------------------------------
# 索引与 memory-map 追加
# ---------------------------------------------------------------------------


def append_index_row(index: Path, row: str) -> None:
    existing = read_text(index)
    if row in existing:
        return
    ensure_dir(index.parent)
    with index.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write(row)


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


def update_plan_index(index: Path, args: argparse.Namespace, plan_path: Path) -> None:
    row = f"| {today()} | `{args.domain}` | `{args.status}` | {args.title} | [{plan_path.name}]({plan_path.name}) |\n"
    append_index_row(index, row)


def update_conversation_index(index: Path, args: argparse.Namespace, conversation_path: Path) -> None:
    row = (
        f"| {today()} | `{args.domain}` | {args.title} | `{args.promote}` | "
        f"[{conversation_path.name}]({conversation_path.name}) |\n"
    )
    append_index_row(index, row)


def collect_keywords(*parts: str, extra: "list[str] | None" = None) -> str:
    """萃取 memory-map 行关键词：20 词 + 120 字符双重上限（C1 预算管制）。"""
    words: "list[str]" = []
    for part in parts:
        words.extend(re.findall(r"[\w一-鿿]+", part or ""))
    words.extend(optional_list(extra))
    seen: "list[str]" = []
    length = 0
    for word in words:
        if not word or word in seen:
            continue
        extra_length = len(word) + (1 if seen else 0)
        if len(seen) >= 20 or length + extra_length > KEYWORDS_MAX_CHARS:
            break
        seen.append(word)
        length += extra_length
    return " ".join(seen) or "general"


def update_memory_map(
    layout: Layout,
    config: ProjectConfig,
    *,
    record_type: str,
    status: str,
    domain: str,
    keywords: str,
    record_path: Path,
    description: str,
) -> None:
    memory_map = layout.fengwang_dir / "memory-map.md"
    if not memory_map.exists():
        write_text(memory_map, memory_map_template(config))
    link = f"[{record_path.name}]({os.path.relpath(record_path, memory_map.parent)})"
    row = f"| {record_type} | {status} | {domain} | {keywords} | {link} | {description} |\n"
    append_index_row(memory_map, row)


def upsert_memory_map_row(
    layout: Layout,
    config: ProjectConfig,
    *,
    record_type: str,
    status: str,
    domain: str,
    keywords: str,
    record_path: Path,
    description: str,
) -> None:
    """受管文件（project-facts.md）的 memory-map 行必须幂等：同一目标只保留一行。

    与 update_memory_map 的 append 语义相反——事实登记会反复写同一个文件，追加会让
    memory-map 长出 N 行指向同一目标，污染路由。已有行则就地替换并累积触发词。
    """
    memory_map = layout.fengwang_dir / "memory-map.md"
    if not memory_map.exists():
        write_text(memory_map, memory_map_template(config))
    target = os.path.relpath(record_path, memory_map.parent)
    link = f"[{record_path.name}]({target})"
    text = read_text(memory_map)

    lines = text.splitlines(keepends=True)
    replaced = False
    for idx, line in enumerate(lines):
        if not (line.strip().startswith("|") and f"]({target})" in line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        if replaced:
            lines[idx] = ""  # 历史遗留的重复行一并收敛掉
            continue
        # 累积旧触发词（新词在前），仍受 collect_keywords 的双重上限管制
        merged = collect_keywords(keywords, cells[3])
        lines[idx] = f"| {record_type} | {status} | {domain} | {merged} | {link} | {description} |\n"
        replaced = True
    if replaced:
        write_text(memory_map, "".join(lines))
    else:
        append_index_row(memory_map, f"| {record_type} | {status} | {domain} | {keywords} | {link} | {description} |\n")


# ---------------------------------------------------------------------------
# B4：真相层 delta 语义合并（红线 9：同一规则同一时刻只有一个现行条目）
# ---------------------------------------------------------------------------


def find_section(lines: "list[str]", titles: "tuple[str, ...]") -> "tuple[int, int]":
    """返回 (标题行下标, 段结束下标)；段结束 = 下一个二级标题或文件尾。未找到返回 (-1, -1)。"""
    for idx, line in enumerate(lines):
        if line.strip() in titles:
            end = idx + 1
            while end < len(lines) and not lines[end].startswith("## "):
                end += 1
            return idx, end
    return -1, -1


def parse_rule_blocks(
    lines: "list[str]", start: int, end: int, heading_re: "re.Pattern[str]" = RULE_HEADING_RE
) -> "dict[str, tuple[int, int]]":
    """解析段内 `### 规则：<名>` 块，返回 规则名 → (块起始行, 块结束行)。

    heading_re 可换成 FACT_HEADING_RE 以复用于项目事实登记（同构的稳定 key 语义）。
    """
    blocks: "dict[str, tuple[int, int]]" = {}
    idx = start + 1
    current_name = ""
    current_start = -1
    while idx < end:
        match = heading_re.match(lines[idx])
        if match:
            if current_name:
                blocks[current_name] = (current_start, idx)
            current_name = match.group(1).strip()
            current_start = idx
        idx += 1
    if current_name:
        blocks[current_name] = (current_start, end)
    return blocks


def extract_links_from_lines(lines: "list[str]", field_markers: "tuple[str, ...]") -> "list[str]":
    links: "list[str]" = []
    for line in lines:
        if any(marker in line for marker in field_markers):
            links.extend(re.findall(r"\[[^\]]+\]\([^)]+\)", line))
    return links


def render_rule_block(
    *,
    name: str,
    rule: str,
    scenario: str,
    source_link: str,
    date: str,
    history_links: "list[str]",
    en: bool,
) -> "list[str]":
    """按附录 B 渲染规则条目。沿革仅在 modified 后存在。"""
    if en:
        lines = [
            f"### Rule: {name}",
            f"- **Rule**：{rule}",
            f"- **Scenario**：{scenario or 'to fill in'}",
            f"- **Source**：{source_link}",
            f"- **Effective**：{date}",
        ]
        if history_links:
            lines.append(f"- **History**：{'、'.join(history_links)}")
    else:
        lines = [
            f"### 规则：{name}",
            f"- **规则**：{rule}",
            f"- **场景**：{scenario or '待补充'}",
            f"- **来源**：{source_link}",
            f"- **生效**：{date}",
        ]
        if history_links:
            lines.append(f"- **沿革**：{'、'.join(history_links)}")
    return lines


def merge_domain_rule(
    text: str,
    *,
    kind: str,
    name: str,
    rule: str,
    scenario: str,
    task_label: str,
    task_link: str,
    date: str,
    en: bool = False,
) -> "tuple[str, list[Diagnostic]]":
    """对 domain 文件执行 added/modified/removed 语义合并。

    失败时返回原文和 error 诊断，调用方必须整体失败、不落任何盘（先验证后写入）。
    """
    diagnostics: "list[Diagnostic]" = []
    lines = text.splitlines()
    source_link = f"[{task_label}]({task_link})"

    sec_start, sec_end = find_section(lines, CURRENT_RULES_TITLES)
    if sec_start == -1:
        if kind in ("modified", "removed"):
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="rule_not_found",
                    message=f"domain 文件没有『当前业务规则』段，找不到规则「{name}」",
                    fix="核对规则名与 domain 文件结构，或改用 --change-kind added",
                )
            )
            return text, diagnostics
        # added：文件缺段则在末尾补一个段
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(CURRENT_RULES_TITLES[1 if en else 0])
        lines.append("")
        sec_start = len(lines) - 2
        sec_end = len(lines)

    blocks = parse_rule_blocks(lines, sec_start, sec_end)

    if kind == "added":
        if name in blocks:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="rule_already_exists",
                    message=f"规则「{name}」已存在，added 不允许覆盖",
                    target=name,
                    fix="改用 --change-kind modified；或确认确是新规则后换一个规则名",
                )
            )
            return text, diagnostics
        block = render_rule_block(
            name=name, rule=rule, scenario=scenario, source_link=source_link,
            date=date, history_links=[], en=en,
        )
        # 去掉空段占位行
        body = [
            line for line in lines[sec_start + 1 : sec_end]
            if line.strip() not in (EMPTY_RULES_PLACEHOLDER_ZH, EMPTY_RULES_PLACEHOLDER_EN)
        ]
        while body and not body[-1].strip():
            body.pop()
        new_body = body + ["", *block, ""] if body else ["", *block, ""]
        lines = lines[: sec_start + 1] + new_body + lines[sec_end:]
        return "\n".join(lines) + ("\n" if text.endswith("\n") or not text else ""), diagnostics

    if name not in blocks:
        candidates = difflib.get_close_matches(name, list(blocks.keys()), n=3, cutoff=0.3)
        hint = f"；现有规则：{'、'.join(blocks.keys()) or '（无）'}"
        if candidates:
            hint += f"；最相近候选：{'、'.join(candidates)}"
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="rule_not_found",
                message=f"规则「{name}」不存在{hint}",
                target=name,
                fix="核对规则名（稳定 key 不随内容变化），或改用 --change-kind added",
            )
        )
        return text, diagnostics

    block_start, block_end = blocks[name]
    old_block = lines[block_start:block_end]

    if kind == "modified":
        # 保链不保文：新沿革 = 旧来源链接 + 旧沿革链接（最近的在前）
        old_source = extract_links_from_lines(old_block, ("**来源**", "**Source**"))
        old_history = extract_links_from_lines(old_block, ("**沿革**", "**History**"))
        block = render_rule_block(
            name=name, rule=rule, scenario=scenario, source_link=source_link,
            date=date, history_links=old_source + old_history, en=en,
        )
        while block_end > block_start and not lines[block_end - 1].strip():
            block_end -= 1
        lines = lines[:block_start] + block + lines[block_end:]
        return "\n".join(lines) + ("\n" if text.endswith("\n") or not text else ""), diagnostics

    # removed：从现行段移除，追加到已废除段
    retired_line = (
        f"- ~~{name}~~: retired {date} by {source_link}"
        if en
        else f"- ~~{name}~~：{date} 由 {source_link} 废除"
    )
    del lines[block_start:block_end]
    ret_start, ret_end = find_section(lines, RETIRED_RULES_TITLES)
    if ret_start == -1:
        # 缺已废除段则紧跟现行段之后补一个
        cur_start, cur_end = find_section(lines, CURRENT_RULES_TITLES)
        insert_at = cur_end if cur_start != -1 else len(lines)
        lines[insert_at:insert_at] = ["", RETIRED_RULES_TITLES[1 if en else 0], "", retired_line]
    else:
        body = [
            line for line in lines[ret_start + 1 : ret_end]
            if line.strip() not in (EMPTY_RETIRED_PLACEHOLDER_ZH, EMPTY_RETIRED_PLACEHOLDER_EN)
        ]
        while body and not body[-1].strip():
            body.pop()
        new_body = body + [retired_line] if body else ["", retired_line]
        if new_body[-1].strip():
            new_body.append("")
        lines = lines[: ret_start + 1] + new_body + lines[ret_end:]
    return "\n".join(lines) + ("\n" if text.endswith("\n") or not text else ""), diagnostics


# ---------------------------------------------------------------------------
# F-007：项目事实登记合并（与红线 9 同构——一个事实名只有一条现行值）
# ---------------------------------------------------------------------------


DEFAULT_FACT_KIND = "general"


def extract_field_value(lines: "list[str]", field_markers: "tuple[str, ...]") -> str:
    """取条目中某个 `- **字段**：值` 行的值；找不到返回空串。"""
    for line in lines:
        for marker in field_markers:
            if marker in line:
                _, _, value = line.partition("：" if "：" in line else ":")
                return value.strip()
    return ""


def parse_confirmed_fact(raw: str) -> "tuple[str, str] | None":
    """解析 `名称=值` 入参；名称不含 `=`，值可以含（如 URL 查询串）。"""
    if "=" not in (raw or ""):
        return None
    name, _, value = raw.partition("=")
    name, value = name.strip(), value.strip()
    if not name or not value:
        return None
    return name, value


def render_fact_block(
    *,
    name: str,
    value: str,
    kind: str,
    source_link: str,
    date: str,
    history_links: "list[str]",
    en: bool,
) -> "list[str]":
    """渲染事实条目；沿革仅在覆盖旧值后存在（保链不保文，与规则条目同构）。"""
    if en:
        lines = [
            f"### Fact: {name}",
            f"- **Kind**：{kind}",
            f"- **Value**：{value}",
            f"- **Source**：{source_link}",
            f"- **Updated**：{date}",
        ]
        if history_links:
            lines.append(f"- **History**：{'、'.join(history_links)}")
    else:
        lines = [
            f"### 事实：{name}",
            f"- **类别**：{kind}",
            f"- **事实**：{value}",
            f"- **来源**：{source_link}",
            f"- **更新**：{date}",
        ]
        if history_links:
            lines.append(f"- **沿革**：{'、'.join(history_links)}")
    return lines


def merge_project_fact(
    text: str,
    *,
    name: str,
    value: str,
    kind: str,
    source_label: str,
    source_link: str,
    date: str,
    en: bool = False,
) -> "tuple[str, list[Diagnostic], str]":
    """登记一条确凿事实：同名则覆盖（旧来源转入沿革），否则新增。

    返回 (新文本, 诊断, 动作)，动作为 added/updated。与 maintain 不同，事实登记的
    added/updated 由稳定 key 自动判定——事实名相同就是同一件事，不需要调用方指明。
    """
    diagnostics: "list[Diagnostic]" = []
    lines = text.splitlines()
    link = f"[{source_label}]({source_link})"

    sec_start, sec_end = find_section(lines, CURRENT_FACTS_TITLES)
    if sec_start == -1:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(CURRENT_FACTS_TITLES[1 if en else 0])
        lines.append("")
        sec_start = len(lines) - 2
        sec_end = len(lines)

    blocks = parse_rule_blocks(lines, sec_start, sec_end, FACT_HEADING_RE)

    if name in blocks:
        block_start, block_end = blocks[name]
        old_block = lines[block_start:block_end]
        old_source = extract_links_from_lines(old_block, ("**来源**", "**Source**"))
        old_history = extract_links_from_lines(old_block, ("**沿革**", "**History**"))
        # 未显式指定类别时沿用旧类别，避免覆盖值时把分类静默洗成 general
        if kind == DEFAULT_FACT_KIND:
            kind = extract_field_value(old_block, ("**类别**", "**Kind**")) or kind
        block = render_fact_block(
            name=name, value=value, kind=kind, source_link=link,
            date=date, history_links=old_source + old_history, en=en,
        )
        while block_end > block_start and not lines[block_end - 1].strip():
            block_end -= 1
        lines = lines[:block_start] + block + lines[block_end:]
        action = "updated"
    else:
        block = render_fact_block(
            name=name, value=value, kind=kind, source_link=link,
            date=date, history_links=[], en=en,
        )
        body = [
            line for line in lines[sec_start + 1 : sec_end]
            if line.strip() not in (EMPTY_FACTS_PLACEHOLDER_ZH, EMPTY_FACTS_PLACEHOLDER_EN)
        ]
        while body and not body[-1].strip():
            body.pop()
        lines = lines[: sec_start + 1] + body + ["", *block, ""] + lines[sec_end:]
        action = "added"
    return "\n".join(lines) + ("\n" if text.endswith("\n") or not text else ""), diagnostics, action


def retire_project_fact(
    text: str,
    *,
    name: str,
    source_label: str,
    source_link: str,
    date: str,
    en: bool = False,
) -> "tuple[str, list[Diagnostic]]":
    """废除一条现行事实：移出现行段，追加到已失效段。事实不存在时报错、不落盘。"""
    diagnostics: "list[Diagnostic]" = []
    lines = text.splitlines()
    link = f"[{source_label}]({source_link})"

    sec_start, sec_end = find_section(lines, CURRENT_FACTS_TITLES)
    blocks = parse_rule_blocks(lines, sec_start, sec_end, FACT_HEADING_RE) if sec_start != -1 else {}
    if name not in blocks:
        candidates = difflib.get_close_matches(name, list(blocks.keys()), n=3, cutoff=0.3)
        hint = f"；现有事实：{'、'.join(blocks.keys()) or '（无）'}"
        if candidates:
            hint += f"；最相近候选：{'、'.join(candidates)}"
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="fact_not_found",
                message=f"事实「{name}」不存在{hint}",
                target=name,
                fix="核对事实名（稳定 key 不随值变化）；若只是值变了，用 --confirmed-fact 覆盖即可",
            )
        )
        return text, diagnostics

    block_start, block_end = blocks[name]
    retired_line = (
        f"- ~~{name}~~: retired {date} by {link}"
        if en
        else f"- ~~{name}~~：{date} 由 {link} 废除"
    )
    del lines[block_start:block_end]
    ret_start, ret_end = find_section(lines, RETIRED_FACTS_TITLES)
    if ret_start == -1:
        cur_start, cur_end = find_section(lines, CURRENT_FACTS_TITLES)
        insert_at = cur_end if cur_start != -1 else len(lines)
        lines[insert_at:insert_at] = ["", RETIRED_FACTS_TITLES[1 if en else 0], "", retired_line]
    else:
        body = [
            line for line in lines[ret_start + 1 : ret_end]
            if line.strip() not in (EMPTY_RETIRED_PLACEHOLDER_ZH, EMPTY_RETIRED_PLACEHOLDER_EN)
        ]
        while body and not body[-1].strip():
            body.pop()
        new_body = body + [retired_line] if body else ["", retired_line]
        if new_body[-1].strip():
            new_body.append("")
        lines = lines[: ret_start + 1] + new_body + lines[ret_end:]
    return "\n".join(lines) + ("\n" if text.endswith("\n") or not text else ""), diagnostics


# ---------------------------------------------------------------------------
# 链接校验与 git 变更
# ---------------------------------------------------------------------------


def check_links(root: Path, markdown_file: Path) -> "list[Diagnostic]":
    diagnostics: "list[Diagnostic]" = []
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
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="broken_link",
                    message=(
                        f"Broken link in {markdown_file.relative_to(root)}: "
                        f"{link} -> {target_path.relative_to(root.resolve())}"
                    ),
                    target=str(markdown_file.relative_to(root)),
                    fix="确认目标文件是否被误删、改名或归档；修正链接后重跑 check",
                )
            )
    return diagnostics


def memory_markdown_files(layout: Layout) -> "list[Path]":
    files: "dict[Path, None]" = {}
    for directory in layout.memory_dirs():
        if not directory.exists():
            continue
        if directory == layout.memory_root and not layout.is_legacy:
            # 新布局：记忆根本身就包含全部层，只扫一次并排除工具目录
            for markdown_file in directory.rglob("*.md"):
                files[markdown_file] = None
        else:
            for markdown_file in directory.rglob("*.md"):
                files[markdown_file] = None
    return list(files.keys())


def link_error_diagnostics(project: Path, layout: Layout) -> "list[Diagnostic]":
    diagnostics: "list[Diagnostic]" = []
    for markdown_file in memory_markdown_files(layout):
        diagnostics.extend(check_links(project, markdown_file))
    return diagnostics


def git_changed_files(project: Path) -> "list[str]":
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
    changed: "list[str]" = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        entry = line[3:].strip()
        # rename 格式 "old -> new"，取新路径
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        changed.append(entry.strip('"'))
    return changed


def memory_path_prefixes(config: ProjectConfig) -> "list[str]":
    prefixes = [".fengchao/"]
    if config.memory_root:
        prefixes.append(config.memory_root + "/")
    else:
        for name in (
            config.context_dir,
            config.task_dir,
            config.changelog_dir,
            config.plan_dir,
            config.conversation_dir,
            config.fengwang_dir,
        ):
            prefixes.append(name + "/")
    return prefixes


def project_change_paths(project: Path, config: ProjectConfig) -> "list[str]":
    prefixes = tuple(memory_path_prefixes(config))
    return [item for item in git_changed_files(project) if not item.startswith(prefixes)]


def collect_check_diagnostics(
    project: Path,
    config: ProjectConfig,
    layout: Layout,
    *,
    require_records: bool,
) -> "list[Diagnostic]":
    diagnostics: "list[Diagnostic]" = []
    required = [
        project / ".fengchao" / "config.yaml",
        layout.fengwang_dir / "FENGWANG.md",
        layout.fengwang_dir / "memory-map.md",
        layout.context_dir / "CONTEXT-INDEX.md",
        layout.plan_dir / "PLAN-INDEX.md",
        layout.conversation_dir / "CONVERSATION-INDEX.md",
        layout.task_dir / "TASK-INDEX.md",
        layout.changelog_dir / "CHANGELOG-INDEX.md",
    ]
    for path in required:
        if not path.exists():
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="missing_required_file",
                    message=f"Missing required file: {path.relative_to(project)}",
                    target=str(path.relative_to(project)),
                    fix="运行 `fengchao.py init` 补齐脚手架（已有文件不会被覆盖）",
                )
            )

    diagnostics.extend(link_error_diagnostics(project, layout))

    memory_map = layout.fengwang_dir / "memory-map.md"
    if memory_map.exists():
        for row in parse_memory_map_rows(read_text(memory_map)):
            if len(row.keywords) > KEYWORDS_MAX_CHARS:
                diagnostics.append(
                    Diagnostic(
                        severity="warning",
                        code="memory_map_row_too_long",
                        message=f"memory-map 行 keywords 超过 {KEYWORDS_MAX_CHARS} 字符：{row.link_label}",
                        target=row.link_target,
                        fix="精简该行触发词，或运行 `fengchao.py compact` 重建 memory-map",
                    )
                )

    if require_records:
        changes = project_change_paths(project, config)
        if changes:
            has_changelog_today = bool(list(layout.changelog_dir.glob(f"{today()}_*.md")))
            has_task_today = bool(list(layout.task_dir.glob(f"{today()}_*.md")))
            if not has_changelog_today:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="missing_changelog_for_changes",
                        message="检测到项目 git 变更，但当天没有任何 changelog 记录",
                        fix="真实交付后运行 `fengchao.py maintain --title ... --summary ... --implementation ...`（lite 交付也会写 changelog）",
                    )
                )
                if not has_task_today:
                    diagnostics.append(
                        Diagnostic(
                            severity="warning",
                            code="missing_task_record_for_changes",
                            message="当天也没有 task-record（lite 交付只需 changelog，可忽略；full 交付请补 task-record）",
                            fix="如本次交付有业务含义，用 --business-change 走 full 档",
                        )
                    )
    return diagnostics


def check_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    layout = resolve_layout(project, config)
    require = bool(args.strict or args.require_records_for_git_changes)
    diagnostics = collect_check_diagnostics(project, config, layout, require_records=require)
    return emit_envelope(
        "check",
        diagnostics,
        fmt=args.format,
        ok_message="FengChao check passed",
        warn_mode=bool(args.warn),
    )


# ---------------------------------------------------------------------------
# maintain：B5 分档（lite/full）+ B4 先验证后写入
# ---------------------------------------------------------------------------


def maintain_project(project: Path, args: argparse.Namespace) -> int:
    fmt = args.format
    config = load_config(project)
    layout = resolve_layout(project, config)
    en = is_en(config)
    # B5：有业务含义的交付才走 full 档
    tier = "full" if args.business_change else "lite"
    write_task = tier == "full" or args.with_task_record

    if tier == "full" and not args.rule_name:
        print(
            "maintain: 提供 --business-change 时必须同时提供 --rule-name（B4 稳定 key），"
            "并用 --change-kind 指明 added/modified/removed",
            file=sys.stderr,
        )
        return EXIT_USAGE

    ensure_dir(layout.task_dir)
    ensure_dir(layout.changelog_dir)
    write_if_missing(layout.task_dir / "TASK-INDEX.md", task_index_template(config))
    write_if_missing(layout.changelog_dir / "CHANGELOG-INDEX.md", changelog_index_template(config))

    # 来源链接统一为记忆根相对完整路径（裸记录名、记忆根相对、项目根相对写法都接受）
    args.from_plan = normalize_memory_relative(args.from_plan, config, config.plan_dir)
    args.from_conversation = normalize_memory_relative(
        args.from_conversation, config, config.conversation_dir
    )

    task_path = next_record_path(layout.task_dir, args.title) if write_task else None
    changelog_path = next_record_path(layout.changelog_dir, args.title)

    # B4：先在内存中完成语义合并，失败则整体失败、不写任何文件
    merged_domain_text = None
    domain_path = None
    if tier == "full":
        domain_path = layout.context_dir / "domains" / f"domain-{slugify(args.domain)}.md"
        base_text = read_text(domain_path) or domain_template(config, args.domain)
        merged_domain_text, merge_diags = merge_domain_rule(
            base_text,
            kind=args.change_kind,
            name=args.rule_name,
            rule=args.business_change,
            scenario=args.scenario or "",
            task_label=task_path.name,
            task_link=f"../../{config.task_dir}/{task_path.name}",
            date=today(),
            en=en,
        )
        if any(d.severity == "error" for d in merge_diags):
            return emit_envelope("maintain", merge_diags, fmt=fmt)

    created: "list[str]" = []
    if write_task:
        write_text(task_path, task_record_content(config, args, changelog_path.name))
        update_task_index(layout.task_dir / "TASK-INDEX.md", args, task_path)
        created.append(str(task_path.relative_to(project)))
    write_text(changelog_path, changelog_content(config, args, task_path.name if write_task else ""))
    update_changelog_index(layout.changelog_dir / "CHANGELOG-INDEX.md", args, changelog_path)
    created.append(str(changelog_path.relative_to(project)))

    if merged_domain_text is not None:
        write_text(domain_path, merged_domain_text)
        created.append(str(domain_path.relative_to(project)))

    keywords = collect_keywords(args.title, args.summary, args.business_change, args.implementation)
    if write_task:
        update_memory_map(
            layout,
            config,
            record_type="task",
            status="implemented",
            domain=args.domain,
            keywords=keywords,
            record_path=task_path,
            description="已落地开发任务" if not en else "Landed development task",
        )
    update_memory_map(
        layout,
        config,
        record_type="changelog",
        status="historical",
        domain=args.domain,
        keywords=keywords,
        record_path=changelog_path,
        description="已落地变更记录" if not en else "Landed change record",
    )

    # B4 步骤 4：合并完成后自动跑链接校验
    diagnostics: "list[Diagnostic]" = []
    if tier == "full":
        diagnostics = link_error_diagnostics(project, layout)

    payload = {"tier": tier, "created": created}
    if fmt == "json":
        return emit_envelope("maintain", diagnostics, fmt="json", payload=payload)
    for path in created:
        print(f"created {path}")
    print(f"tier: {tier}")
    if diagnostics:
        return emit_envelope("maintain", diagnostics, fmt="text")
    return EXIT_OK


# ---------------------------------------------------------------------------
# plan / conversation / inspect
# ---------------------------------------------------------------------------


def plan_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    layout = resolve_layout(project, config)
    ensure_dir(layout.plan_dir)
    write_if_missing(layout.plan_dir / "PLAN-INDEX.md", plan_index_template(config))
    plan_path = next_record_path(layout.plan_dir, args.title)
    write_text(plan_path, plan_record_content(config, args))
    update_plan_index(layout.plan_dir / "PLAN-INDEX.md", args, plan_path)
    update_memory_map(
        layout,
        config,
        record_type="plan",
        status=args.status,
        domain=args.domain,
        keywords=collect_keywords(args.title, args.goal, args.plan, extra=args.assumption),
        record_path=plan_path,
        description="计划阶段记录，非当前业务事实" if not is_en(config) else "Plan-stage record, not current truth",
    )
    print(f"created {plan_path.relative_to(project)}")
    return EXIT_OK


def conversation_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    layout = resolve_layout(project, config)
    en = is_en(config)
    fmt = getattr(args, "format", "text")
    confirmed = list(args.confirmed_fact or [])
    retired = list(args.retire_fact or [])

    # 先验证：入参格式错误必须在任何落盘之前失败（与 B4 同纪律）
    parsed: "list[tuple[str, str]]" = []
    for raw in confirmed:
        pair = parse_confirmed_fact(raw)
        if pair is None:
            diag = Diagnostic(
                severity="error",
                code="invalid_fact_format",
                message=f"--confirmed-fact 需要 `名称=值` 格式，收到：{raw}",
                target=raw,
                fix='例：--confirmed-fact "设计单提交审核入口=POST /liangang/workorder/submitReview"',
            )
            return emit_envelope("conversation", [diag], fmt=fmt)
        parsed.append(pair)

    conversation_path = next_record_path(layout.conversation_dir, args.title)
    facts_path = layout.context_dir / PROJECT_FACTS_FILE
    # 事实来源指向本次对话记录（相对 project-facts.md 所在目录）
    source_link = f"../{config.conversation_dir}/{conversation_path.name}"

    # 先合并：全部事实在内存中完成，任一失败则整体失败，连对话记录都不写
    merged_facts_text = None
    actions: "list[str]" = []
    if parsed or retired:
        merged_facts_text = read_text(facts_path) or project_facts_template(config)
        for name, value in parsed:
            merged_facts_text, diags, action = merge_project_fact(
                merged_facts_text,
                name=name,
                value=value,
                kind=args.fact_kind,
                source_label=conversation_path.name,
                source_link=source_link,
                date=today(),
                en=en,
            )
            if any(d.severity == "error" for d in diags):
                return emit_envelope("conversation", diags, fmt=fmt)
            actions.append(f"{action} {name}")
        for name in retired:
            merged_facts_text, diags = retire_project_fact(
                merged_facts_text,
                name=name,
                source_label=conversation_path.name,
                source_link=source_link,
                date=today(),
                en=en,
            )
            if any(d.severity == "error" for d in diags):
                return emit_envelope("conversation", diags, fmt=fmt)
            actions.append(f"retired {name}")

    ensure_dir(layout.conversation_dir)
    write_if_missing(layout.conversation_dir / "CONVERSATION-INDEX.md", conversation_index_template(config))
    write_text(conversation_path, conversation_record_content(config, args))
    update_conversation_index(layout.conversation_dir / "CONVERSATION-INDEX.md", args, conversation_path)
    update_memory_map(
        layout,
        config,
        record_type="conversation",
        status="historical",
        domain=args.domain,
        keywords=collect_keywords(args.title, args.summary, extra=args.term + args.preference + args.rejected),
        record_path=conversation_path,
        description="用户业务解释和偏好，非当前业务事实" if not en else "User explanation, not current truth",
    )

    created = [str(conversation_path.relative_to(project))]
    if merged_facts_text is not None:
        ensure_dir(facts_path.parent)
        write_text(facts_path, merged_facts_text)
        created.append(str(facts_path.relative_to(project)))
        # 事实名与值本身就是最好的触发词，优先入 keywords 以提升后续路由命中
        upsert_memory_map_row(
            layout,
            config,
            record_type="fact",
            status="current",
            domain=args.domain,
            keywords=collect_keywords(
                *[f"{name} {value}" for name, value in parsed],
                args.fact_kind,
                extra=["事实", "入口", "配置", "约定"] if not en else ["fact", "entry", "config", "convention"],
            ),
            record_path=facts_path,
            description="用户确认的项目事实登记" if not en else "User-confirmed project facts",
        )

    # 事实写入真相层后自动跑链接校验（与 maintain full 档同纪律）
    diagnostics = link_error_diagnostics(project, layout) if merged_facts_text is not None else []
    if fmt == "json":
        return emit_envelope(
            "conversation", diagnostics, fmt="json", payload={"created": created, "facts": actions}
        )
    for path in created:
        print(f"created {path}")
    for action in actions:
        print(f"fact: {action}")
    if diagnostics:
        return emit_envelope("conversation", diagnostics, fmt="text")
    return EXIT_OK


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
    return EXIT_OK


# ---------------------------------------------------------------------------
# FengWang 路由 v2：结构化解析 + 词级打分 + 预算管制（C1，纯函数可单测）
# ---------------------------------------------------------------------------


@dataclass
class MemoryRow:
    record_type: str
    status: str
    domain: str
    keywords: str
    link_label: str
    link_target: str
    description: str
    date: str
    raw: str


def parse_memory_map_rows(text: str) -> "list[MemoryRow]":
    rows: "list[MemoryRow]" = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 6:
            continue
        # 跳过表头与分隔行（兼容中英文表头）
        if cells[0] in ("类型", "Type"):
            continue
        if set(cells[0]) <= set("-: "):
            continue
        link_match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", cells[4])
        label = link_match.group(1) if link_match else cells[4]
        target = link_match.group(2) if link_match else ""
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})_", target or label)
        rows.append(
            MemoryRow(
                record_type=cells[0],
                status=cells[1],
                domain=cells[2],
                keywords=cells[3],
                link_label=label,
                link_target=target,
                description=cells[5],
                date=date_match.group(1) if date_match else "",
                raw=line,
            )
        )
    return rows


def tokenize_for_scoring(text: str) -> "list[str]":
    """中文按 2-gram、英文按词切分（全部 stdlib，零依赖红线）。"""
    tokens: "list[str]" = []
    lowered = (text or "").lower()
    tokens.extend(re.findall(r"[a-z0-9_]+", lowered))
    for chunk in re.findall(r"[一-鿿]+", lowered):
        if len(chunk) == 1:
            tokens.append(chunk)
        else:
            tokens.extend(chunk[i : i + 2] for i in range(len(chunk) - 1))
    return tokens


TYPE_BONUS = {"context": 1.5, "fact": 1.5, "conversation": 0.5, "plan": 0.5}


def score_memory_rows(
    query: str, rows: "list[MemoryRow]", reference_date: "str | None" = None
) -> "list[tuple[float, MemoryRow]]":
    """路由打分纯函数：词级匹配 + IDF 加权 + 领域命中加权 + 时间衰减 + 类型加权。"""
    reference_date = reference_date or today()
    query_tokens = set(tokenize_for_scoring(query))
    if not query_tokens or not rows:
        return []
    docs = [
        set(
            tokenize_for_scoring(
                " ".join([row.keywords, row.description, row.domain, row.record_type, row.link_label])
            )
        )
        for row in rows
    ]
    df: "dict[str, int]" = {}
    for doc in docs:
        for token in doc:
            df[token] = df.get(token, 0) + 1
    total = len(rows)
    try:
        ref = dt.date.fromisoformat(reference_date)
    except ValueError:
        ref = dt.date.today()

    scored: "list[tuple[float, MemoryRow]]" = []
    for row, doc in zip(rows, docs):
        matched = query_tokens & doc
        if not matched:
            continue
        # 罕见词命中权重高于高频词（IDF 式加权）
        score = sum(1.0 + math.log((total + 1) / (df.get(token, 0) + 1)) for token in matched)
        if query_tokens & set(tokenize_for_scoring(row.domain)):
            score += 2.0
        score += TYPE_BONUS.get(row.record_type, 0.0)
        if row.date:
            try:
                age_days = (ref - dt.date.fromisoformat(row.date)).days
                if age_days <= 30:
                    score += 1.0
                elif age_days <= 90:
                    score += 0.5
            except ValueError:
                pass
        scored.append((score, row))
    # 分数降序；同分时近期记录优先
    scored.sort(key=lambda item: (item[0], item[1].date), reverse=True)
    return scored


def fengwang_query(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    layout = resolve_layout(project, config)
    memory_map = layout.fengwang_dir / "memory-map.md"
    if not memory_map.exists():
        diag = Diagnostic(
            severity="error",
            code="missing_required_file",
            message=f"Missing {memory_map.relative_to(project)}",
            target=str(memory_map.relative_to(project)),
            fix="运行 `fengchao.py init` 初始化记忆脚手架",
        )
        return emit_envelope("fengwang", [diag], fmt=args.format)

    rows = parse_memory_map_rows(read_text(memory_map))
    scored = score_memory_rows(args.query, rows)[: args.limit]

    results = []
    for idx, (score, row) in enumerate(scored, start=1):
        results.append(
            {
                "rank": idx,
                "target": row.link_target or row.link_label,
                "type": row.record_type,
                "domain": row.domain,
                "description": row.description,
                "score": round(score, 3),
            }
        )

    # C1 预算管制：输出限制在字节预算内，超限截断并明示
    budget = max(args.budget, 256)
    header = "FengWang suggested context（先读前 3 条）:"
    lines: "list[str]" = []
    used = len(header.encode("utf-8"))
    shown = 0
    for item in results:
        line = f"{item['rank']}. {item['target']} — {item['type']}/{item['domain']} — {item['description']}"
        line_bytes = len(line.encode("utf-8")) + 1
        if used + line_bytes > budget:
            break
        lines.append(line)
        used += line_bytes
        shown += 1
    truncated = len(results) - shown

    if args.format == "json":
        payload = {
            "query": args.query,
            "results": results[:shown],
            "truncated": truncated,
            "budget_bytes": budget,
        }
        return emit_envelope("fengwang", [], fmt="json", payload=payload)

    print(header)
    for line in lines:
        print(line)
    if truncated > 0:
        print(f"(已截断：还有 {truncated} 条低分匹配，请细化查询词)")
    if not results:
        print(f"No direct match. Read {fengwang_entry_rel(config)} and business-context/CONTEXT-INDEX.md first.")
    return EXIT_OK


# ---------------------------------------------------------------------------
# Hook 硬门禁（B1）：session-start 自动路由提示 / stop-gate 记忆维护门禁
# ---------------------------------------------------------------------------


def read_hook_payload() -> dict:
    """读取 Claude Code hook 协议的 stdin JSON；容错为空。"""
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def resolve_hook_project(cwd: Path) -> Path:
    """hook 专用项目根解析（F-005）：宿主以会话 cwd 调起 hook，cwd 可能在项目子目录。

    优先级：$CLAUDE_PROJECT_DIR（须真含 .fengchao/config.yaml 才采信）→ 从 cwd 向上
    walk-up 查找 → 落回 cwd（维持"未初始化则静默空跑"纪律）。每层仅一次 stat，<500ms 无虞。
    仅 hook 使用：init 必须保持 cwd 语义，其余命令在子目录明确报错是可诊断的失败。
    """
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if env_root:
        candidate = Path(env_root).resolve()
        if (candidate / ".fengchao" / "config.yaml").exists():
            return candidate
    current = cwd.resolve()
    while True:
        if (current / ".fengchao" / "config.yaml").exists():
            return current
        if current.parent == current:
            return cwd
        current = current.parent


def cli_invocation(project: Path) -> str:
    """给 AI 抄写的 CLI 调用前缀：绝对路径带引号，任意 cwd 下可执行（F-005）。"""
    return f'python3 "{project / CLI_RELATIVE}"'


def maintain_skeleton(project: Path, config: ProjectConfig) -> str:
    return (
        f"{cli_invocation(project)} maintain \\\n"
        '  --title "<本次交付标题>" \\\n'
        '  --summary "<用户真实业务诉求>" \\\n'
        '  --implementation "<最终实现方案>" \\\n'
        '  [--business-change "<业务规则变化>" --change-kind added|modified|removed '
        '--rule-name "<规则名>" --scenario "<具体场景>"]'
    )


def hook_project(project: Path, args: argparse.Namespace) -> int:
    # hook 必须快（<500ms）且静默失败：任何异常不影响宿主 agent
    project = resolve_hook_project(project)
    if not (project / ".fengchao" / "config.yaml").exists():
        return EXIT_OK
    config = load_config(project)
    if not config.enabled:
        return EXIT_OK

    if args.event == "session-start":
        entry = fengwang_entry_rel(config)
        mmap = memory_map_rel(config)
        if is_en(config):
            context = (
                f"This project uses FengChao business memory. Read `{entry}` first and route "
                f"the smallest necessary context via `{mmap}` (read the top 3 results first). "
                f"After real development delivery run `{cli_invocation(project)} maintain ...`."
            )
        else:
            context = (
                f"本项目启用 FengChao 业务记忆：先读 `{entry}`，按 `{mmap}` 路由最小必要上下文"
                f"（先读前 3 条）。真实开发交付后运行 `{cli_invocation(project)} maintain ...` 维护记忆。"
            )
        print(
            json.dumps(
                {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}},
                ensure_ascii=False,
            )
        )
        return EXIT_OK

    # stop-gate
    if config.hook_mode == "off":
        return EXIT_OK
    payload = read_hook_payload()
    if payload.get("stop_hook_active"):
        return EXIT_OK
    layout = resolve_layout(project, config)
    if not project_change_paths(project, config):
        return EXIT_OK
    if list(layout.changelog_dir.glob(f"{today()}_*.md")):
        return EXIT_OK
    # 会话级防重：同一 session 最多提醒一次（B1 防打扰设计）
    session_id = slugify(str(payload.get("session_id") or "unknown"))[:64]
    marker = project / ".fengchao" / "tmp" / f"stop-gate-{session_id}"
    if marker.exists():
        return EXIT_OK
    write_text(marker, today())

    skeleton = maintain_skeleton(project, config)
    if config.hook_mode == "strict":
        reason = (
            "FengChao stop-gate：检测到项目 git 变更，但当天没有 changelog 记录。"
            "请先完成记忆维护再结束回复（讨论/只读会话可忽略并说明）：\n" + skeleton
        )
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        return EXIT_OK
    print(
        "FengChao 提醒：本会话存在项目变更但当天无 changelog 记录。"
        "如果确有真实交付，请运行：\n" + skeleton
    )
    return EXIT_OK


def install_git_hook_project(project: Path, args: argparse.Namespace) -> int:
    """可选 git pre-commit 钩子（2.7）：默认不装，装后可干净卸载。"""
    git_dir = project / ".git"
    if not git_dir.is_dir():
        print("当前目录不是 git 仓库根目录", file=sys.stderr)
        return EXIT_FAILURE
    hook_path = git_dir / "hooks" / "pre-commit"
    block = (
        f"{SHELL_MARKER_START}\n"
        f"python3 {CLI_RELATIVE} check --warn --require-records-for-git-changes\n"
        f"{SHELL_MARKER_END}\n"
    )
    if args.remove:
        text = read_text(hook_path)
        if SHELL_MARKER_START not in text:
            print("pre-commit 中没有 FengChao 钩子")
            return EXIT_OK
        pattern = re.compile(
            r"\n*" + re.escape(SHELL_MARKER_START) + r".*?" + re.escape(SHELL_MARKER_END) + r"\n?",
            re.DOTALL,
        )
        updated = pattern.sub("", text, count=1)
        if updated.strip() in ("", "#!/bin/sh"):
            hook_path.unlink()
            print("removed .git/hooks/pre-commit")
        else:
            write_text(hook_path, updated)
            print("removed FengChao block from .git/hooks/pre-commit")
        return EXIT_OK
    if not hook_path.exists():
        write_text(hook_path, "#!/bin/sh\n" + block)
        hook_path.chmod(0o755)
        print("installed .git/hooks/pre-commit")
    else:
        if append_once(hook_path, SHELL_MARKER_START, "\n" + block):
            print("appended FengChao block to .git/hooks/pre-commit")
        else:
            print("FengChao 钩子已存在")
    return EXIT_OK


# ---------------------------------------------------------------------------
# C2：archive / compact / plan-status
# ---------------------------------------------------------------------------


def archive_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    layout = resolve_layout(project, config)
    try:
        dt.date.fromisoformat(args.before)
    except ValueError:
        print(f"--before 需要 YYYY-MM-DD 格式，收到：{args.before}", file=sys.stderr)
        return EXIT_USAGE

    moved: "list[tuple[str, str]]" = []
    for _, directory in layout.record_dirs():
        if not directory.exists():
            continue
        for record in sorted(directory.glob("*.md")):
            match = RECORD_FILE_RE.match(record.name)
            if not match or match.group(1) >= args.before:
                continue
            archive_dir = directory / "archive"
            ensure_dir(archive_dir)
            # 归档文件深一层：相对链接补一级
            # 注意：这里是"前缀追加"（文件下移一层，所有 ../ 统一加深一级），对指向记忆
            # 内部与记忆根之外的链接都保真，与 migrate 的"剥除 ../"（仅内部目标合法，
            # 见 F-003）不同构——不要当成同类 bug 改掉。
            text = read_text(record).replace("](../", "](../../")
            write_text(archive_dir / record.name, text)
            record.unlink()
            moved.append((directory.name, record.name))

    if not moved:
        print(f"没有早于 {args.before} 的记录需要归档")
        return EXIT_OK

    # 改写索引、memory-map 与其他记录中指向已归档记录的链接（链接不断，check 仍通过）
    for markdown_file in memory_markdown_files(layout):
        text = read_text(markdown_file)
        original = text
        for dirname, fname in moved:
            text = text.replace(f"{dirname}/{fname}", f"{dirname}/archive/{fname}")
            if markdown_file.parent.name == dirname:
                text = text.replace(f"]({fname})", f"](archive/{fname})")
        if text != original:
            write_text(markdown_file, text)

    print(f"archived {len(moved)} records (before {args.before})")
    for dirname, fname in moved:
        print(f"  {dirname}/{fname} -> {dirname}/archive/{fname}")
    diagnostics = link_error_diagnostics(project, layout)
    return emit_envelope("archive", diagnostics, fmt="text", ok_message="FengChao check passed")


def serialize_memory_row(row: MemoryRow) -> str:
    link = f"[{row.link_label}]({row.link_target})" if row.link_target else row.link_label
    return f"| {row.record_type} | {row.status} | {row.domain} | {row.keywords} | {link} | {row.description} |"


def compact_project(project: Path, args: argparse.Namespace) -> int:
    """重建 memory-map：去重、按类型和时间重排、归档行折叠到独立段落。"""
    config = load_config(project)
    layout = resolve_layout(project, config)
    memory_map = layout.fengwang_dir / "memory-map.md"
    if not memory_map.exists():
        print(f"Missing {memory_map.relative_to(project)}", file=sys.stderr)
        return EXIT_FAILURE
    rows = parse_memory_map_rows(read_text(memory_map))
    seen: "set[tuple[str, str]]" = set()
    active: "list[MemoryRow]" = []
    archived: "list[MemoryRow]" = []
    duplicates = 0
    for row in rows:
        key = (row.record_type, row.link_target or row.link_label)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        if "/archive/" in row.link_target:
            archived.append(row)
        else:
            active.append(row)

    type_order = {"context": 0, "task": 1, "changelog": 2, "plan": 3, "conversation": 4}

    def sort_key(row: MemoryRow):
        # 无日期的（索引入口行）排最前，其余按日期倒序
        return (type_order.get(row.record_type, 9), 0 if not row.date else 1, row.date and "".join(chr(255 - ord(c)) for c in row.date))

    active.sort(key=sort_key)
    archived.sort(key=sort_key)

    # 表头取自模板（标题 + 引言 + 表头 + 分隔行）
    template_lines = memory_map_template(config).splitlines()
    header_lines: "list[str]" = []
    for line in template_lines:
        header_lines.append(line)
        if set(line.strip().strip("|").replace("|", "")) <= set("-: ") and line.strip().startswith("|"):
            break
    en = is_en(config)
    parts = header_lines + [serialize_memory_row(row) for row in active]
    if archived:
        parts.append("")
        parts.append("## Archived Records" if en else "## 已归档记录")
        parts.append("")
        # 归档段沿用同一张表头（取模板表头最后两行）
        parts.extend(header_lines[-2:])
        parts.extend(serialize_memory_row(row) for row in archived)
    write_text(memory_map, "\n".join(parts) + "\n")
    print(
        f"memory-map rebuilt: {len(active)} active rows, {len(archived)} archived rows, "
        f"{duplicates} duplicates removed"
    )
    return EXIT_OK


PLAN_STATUS_CHOICES = ("proposed", "approved", "superseded", "implemented", "abandoned")


def plan_status_project(project: Path, args: argparse.Namespace) -> int:
    """C2：plan 记录状态流转 + 落地链接回填。"""
    config = load_config(project)
    layout = resolve_layout(project, config)
    candidates = [project / args.record, layout.memory_root / args.record, layout.plan_dir / Path(args.record).name]
    plan_path = next((p for p in candidates if p.is_file()), None)
    if plan_path is None:
        print(f"找不到 plan 记录：{args.record}", file=sys.stderr)
        return EXIT_FAILURE

    text = read_text(plan_path)
    text = re.sub(
        r"(- \*\*(?:计划状态|Plan status)\*\*：).*",
        lambda m: m.group(1) + args.status,
        text,
        count=1,
    )
    if args.link:
        link_candidates = [project / args.link, layout.memory_root / args.link]
        link_path = next((p for p in link_candidates if p.is_file()), None)
        if link_path is None:
            print(f"--link 指向的记录不存在：{args.link}", file=sys.stderr)
            return EXIT_FAILURE
        rel = os.path.relpath(link_path, plan_path.parent)
        for placeholder in ("- task-records：待落地后补充", "- task-records：to fill in after landing"):
            text = text.replace(placeholder, f"- task-records：[{link_path.name}]({rel})")
    write_text(plan_path, text)

    # 同步 PLAN-INDEX 与 memory-map 中该记录行的状态列
    status_pattern = re.compile(r"\| `(?:" + "|".join(PLAN_STATUS_CHOICES) + r")` \|")
    index_path = layout.plan_dir / "PLAN-INDEX.md"
    if index_path.exists():
        lines = read_text(index_path).splitlines()
        for idx, line in enumerate(lines):
            if f"[{plan_path.name}]" in line:
                lines[idx] = status_pattern.sub(f"| `{args.status}` |", line, count=1)
        write_text(index_path, "\n".join(lines) + "\n")
    memory_map = layout.fengwang_dir / "memory-map.md"
    if memory_map.exists():
        lines = read_text(memory_map).splitlines()
        for idx, line in enumerate(lines):
            if plan_path.name in line and line.strip().startswith("|"):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) >= 6 and cells[0] == "plan":
                    cells[1] = args.status
                    lines[idx] = "| " + " | ".join(cells) + " |"
        write_text(memory_map, "\n".join(lines) + "\n")

    print(f"plan {plan_path.name} -> {args.status}" + (f" (linked {args.link})" if args.link else ""))
    return EXIT_OK


# ---------------------------------------------------------------------------
# C3：doctor / migrate
# ---------------------------------------------------------------------------

INDEX_FILE_NAMES = ("TASK-INDEX.md", "CHANGELOG-INDEX.md", "PLAN-INDEX.md", "CONVERSATION-INDEX.md")


def doctor_project(project: Path, args: argparse.Namespace) -> int:
    config = load_config(project)
    layout = resolve_layout(project, config)
    diagnostics: "list[Diagnostic]" = []

    if layout.is_legacy:
        diagnostics.append(
            Diagnostic(
                severity="info",
                code="legacy_layout",
                message="检测到老布局（六个记忆目录散在项目根下）",
                fix="运行 `fengchao.py migrate` 迁移到单一记忆根布局",
            )
        )
    if config.installed_version and config.installed_version != __version__:
        diagnostics.append(
            Diagnostic(
                severity="info",
                code="version_drift",
                message=f"项目内安装版本 {config.installed_version} 落后于当前 CLI {__version__}",
                fix="运行 `fengchao.py upgrade`（不动记忆数据）",
            )
        )

    # 老式追加条目（B4 前的 update_domain_context 产物）：只建议人工整理，不自动转换（红线 8）
    domains_dir = layout.context_dir / "domains"
    if domains_dir.exists():
        for domain_file in sorted(domains_dir.glob("domain-*.md")):
            entries = [
                line for line in read_text(domain_file).splitlines()
                if LEGACY_CONTEXT_ENTRY_RE.match(line.strip())
            ]
            if entries:
                diagnostics.append(
                    Diagnostic(
                        severity="info",
                        code="legacy_context_entry",
                        message=f"{domain_file.relative_to(project)} 存在 {len(entries)} 条老式追加条目",
                        target=str(domain_file.relative_to(project)),
                        fix="人工整理为『当前业务规则』下的规则条目（附录 B 格式），旧内容语义机器拿不准，不自动转换",
                    )
                )

    memory_map = layout.fengwang_dir / "memory-map.md"
    memory_map_text = read_text(memory_map)

    # 孤儿记录：不在任何索引与 memory-map 中
    for name, directory in layout.record_dirs():
        if not directory.exists():
            continue
        index_text = ""
        for index_name in INDEX_FILE_NAMES:
            candidate = directory / index_name
            if candidate.exists():
                index_text = read_text(candidate)
                break
        for record in sorted(directory.glob("*.md")):
            if not RECORD_FILE_RE.match(record.name):
                continue
            if record.name not in index_text and record.name not in memory_map_text:
                diagnostics.append(
                    Diagnostic(
                        severity="warning",
                        code="orphan_record",
                        message=f"记录不在任何索引中：{record.relative_to(project)}",
                        target=str(record.relative_to(project)),
                        fix="把该记录补进对应 INDEX 和 memory-map，或确认属于误建后人工处理",
                    )
                )

    # 死行：索引/memory-map 中链接目标不存在，但同名文件在别处（如已归档未更新行）
    all_memory_files = {p.name: p for p in memory_markdown_files(layout)}
    scan_targets = [memory_map] + [
        directory / index_name
        for _, directory in layout.record_dirs()
        for index_name in INDEX_FILE_NAMES
        if (directory / index_name).exists()
    ]
    for scan_file in scan_targets:
        if not scan_file.exists():
            continue
        for link in LINK_RE.findall(read_text(scan_file)):
            target = link.split("#", 1)[0].strip()
            if not target:
                continue
            target_path = (scan_file.parent / target).resolve()
            if target_path.exists():
                continue
            filename = Path(target).name
            if filename in all_memory_files:
                diagnostics.append(
                    Diagnostic(
                        severity="warning",
                        code="index_dead_row",
                        message=f"{scan_file.relative_to(project)} 中的行指向已移动/归档的 {filename}",
                        target=str(scan_file.relative_to(project)),
                        fix=f"把链接更新为新位置：{all_memory_files[filename].relative_to(project)}",
                    )
                )

    if memory_map.exists():
        for row in parse_memory_map_rows(memory_map_text):
            if len(row.keywords) > KEYWORDS_MAX_CHARS:
                diagnostics.append(
                    Diagnostic(
                        severity="warning",
                        code="memory_map_row_too_long",
                        message=f"memory-map 行 keywords 超过 {KEYWORDS_MAX_CHARS} 字符：{row.link_label}",
                        target=row.link_target,
                        fix="精简触发词或运行 `fengchao.py compact`",
                    )
                )

    # doctor 只建议不失败（红线 8：业务判断留给人）
    ok_message = "doctor: 未发现问题" if not diagnostics else ""
    return emit_envelope("doctor", diagnostics, fmt=args.format, ok_message=ok_message, warn_mode=True)


def migrate_project(project: Path, args: argparse.Namespace) -> int:
    """老布局（六目录散根下）→ 新布局（单一记忆根）一键迁移。"""
    config = load_config(project)
    layout = resolve_layout(project, config)
    if not layout.is_legacy:
        print("已是单一记忆根布局，无需迁移")
        return EXIT_OK
    root_name = args.memory_root or DEFAULT_MEMORY_ROOT
    root = project / root_name
    if root.exists():
        print(f"目标记忆根已存在：{root_name}/，请先处理后重试", file=sys.stderr)
        return EXIT_FAILURE

    ensure_dir(root)
    moved: "list[str]" = []
    for dir_name in (
        config.context_dir,
        config.task_dir,
        config.changelog_dir,
        config.plan_dir,
        config.conversation_dir,
    ):
        source = project / dir_name
        if source.exists():
            shutil.move(str(source), str(root / dir_name))
            moved.append(f"{dir_name}/ -> {root_name}/{dir_name}/")
    fengwang_src = project / config.fengwang_dir
    for fname in ("FENGWANG.md", "memory-map.md"):
        source = fengwang_src / fname
        if source.exists():
            shutil.move(str(source), str(root / fname))
            moved.append(f"{config.fengwang_dir}/{fname} -> {root_name}/{fname}")
    if fengwang_src.exists() and not any(fengwang_src.iterdir()):
        fengwang_src.rmdir()

    # 链接改写：FENGWANG/memory-map 从 fengwang/ 上移到记忆根（同深度），只有指向被搬移
    # 记忆目录的 ../ 需要剥掉；指向记忆根之外项目文件的链接（../docs/x.md 等）必须原样
    # 保留（F-003：新旧位置深度相同，外部链接的 ../ 本就正确）。
    internal_dirs = "|".join(
        re.escape(d)
        for d in (
            config.context_dir,
            config.task_dir,
            config.changelog_dir,
            config.plan_dir,
            config.conversation_dir,
        )
    )
    # 覆盖 markdown 链接 `](../x` 与反引号裸路径 `` `../x `` 两种形态；
    # lookahead 要求目录名后紧跟 / ) ` #，防止 task-records-v2 之类前缀目录被误剥。
    strip_internal_up = re.compile(r"(\]\(|`)\.\./(?=(?:" + internal_dirs + r")(?:[/)`#]))")
    for fname in ("FENGWANG.md", "memory-map.md"):
        path = root / fname
        if path.exists():
            text = strip_internal_up.sub(r"\1", read_text(path))
            write_text(path, text)
    context_root = root / config.context_dir
    if context_root.exists():
        for markdown_file in context_root.rglob("*.md"):
            text = read_text(markdown_file)
            updated = text.replace(f"../{config.fengwang_dir}/", "../")
            if updated != text:
                write_text(markdown_file, updated)

    new_config = replace(config, memory_root=root_name)
    save_config(project, new_config)
    print(f"migrated to single memory root: {root_name}/")
    for item in moved:
        print(f"  {item}")
    print("提示：运行 `fengchao.py upgrade` 可同步刷新宿主注入中的路径")
    diagnostics = link_error_diagnostics(project, resolve_layout(project, new_config))
    return emit_envelope("migrate", diagnostics, fmt="text", ok_message="FengChao check passed")


# ---------------------------------------------------------------------------
# D2：upgrade（升级只动工具本体，绝不触碰记忆根）
# ---------------------------------------------------------------------------


def upgrade_project(project: Path, args: argparse.Namespace) -> int:
    config = require_config(project)
    if config is None:
        return EXIT_FAILURE
    old_version = config.installed_version or "(unknown)"
    print(f"FengChao upgrade: {old_version} -> {__version__}")
    print("将重写（不会触碰记忆根）：")
    print(f"  {SKILL_INSTALL_DIR}/")
    for agent in config.agents:
        for rel in agent_artifact_files(config, agent):
            print(f"  {rel}")
    install_project_skill(project)
    written: "list[str]" = []
    notes: "list[str]" = []
    if config.enabled and config.agents:
        written = install_host_injections(project, config, notes=notes)
    save_config(project, replace(config, installed_version=__version__))
    for path in written:
        print(f"rewritten {path}")
    for note in notes:
        print(f"note: {note}")
    print("upgrade complete（记忆数据未动）")
    return EXIT_OK


# ---------------------------------------------------------------------------
# D1：export-templates —— 从内联模板生成 templates/ 与 adapters/（唯一事实源）
# ---------------------------------------------------------------------------

GENERATED_HEADER_MD = (
    "<!-- 本文件由 `fengchao.py export-templates` 生成，勿手改；"
    "修改请改 fengchao.py 内联模板（DESIGN.md D1） -->\n\n"
)
GENERATED_NOTE = (
    "# 生成产物说明\n\n"
    "本目录内容由 `python3 skills/fengchao-business-memory/scripts/fengchao.py export-templates` 生成，\n"
    "**勿手改**。唯一事实源是 `fengchao.py` 的内联模板函数（DESIGN.md D1）。\n"
    "CI 会校验本目录与内联模板的一致性。\n"
)


def placeholder_export_config() -> ProjectConfig:
    return ProjectConfig(
        project_name="ExampleProject",
        agents=AGENT_CHOICES,
        installed_version=__version__,
    )


def generate_exported_templates() -> "dict[str, str]":
    config = placeholder_export_config()
    date = "YYYY-MM-DD"
    timestamp = "YYYY-MM-DD HH:MM"
    task_args = argparse.Namespace(
        title="<任务标题>",
        domain="<领域>",
        summary="<用户真实业务诉求>",
        business_change="<最终确认的业务规则变化（无则为空走 lite 档）>",
        implementation="<最终实现方案>",
        decision="<关键决策与取舍>",
        risk="<后续风险>",
        change_type="development",
        changed_file=["<变更文件>"],
        evidence=["<实现证据>"],
        validation=["<验证结果>"],
        from_plan=[],
        from_conversation=[],
        rule_name="<规则名（稳定 key）>",
        change_kind="added",
        scenario="<具体场景>",
        with_task_record=False,
    )
    plan_args = argparse.Namespace(
        title="<计划标题>",
        domain="<领域>",
        goal="<用户目标>",
        plan="<最终计划>",
        context="<业务背景>",
        assumption=["<关键假设>"],
        open_question=["<待确认问题>"],
        impact=["<预计影响>"],
        status="proposed",
    )
    conversation_args = argparse.Namespace(
        title="<对话主题>",
        domain="<领域>",
        summary="<用户解释的业务背景>",
        term=["<术语>=<含义>"],
        preference=["<用户偏好或约束>"],
        rejected=["<用户明确否定的方案>"],
        unverified=["<未验证信息>"],
        related=[],
        promote="no",
    )

    files: "dict[str, str]" = {
        "templates/README.md": GENERATED_NOTE,
        "templates/project-config.yaml": dump_config(config),
        "templates/fengwang/FENGWANG.md": GENERATED_HEADER_MD + fengwang_template(config, date),
        "templates/fengwang/memory-map.md": GENERATED_HEADER_MD + memory_map_template(config, date),
        "templates/context/CONTEXT-INDEX.md": GENERATED_HEADER_MD + context_index_template(config, date),
        "templates/context/domain.md": GENERATED_HEADER_MD + domain_template(config, "<领域>", date),
        "templates/context/project-facts.md": GENERATED_HEADER_MD + project_facts_template(config, date),
        "templates/context/impact-matrix.md": GENERATED_HEADER_MD + impact_matrix_template(config),
        "templates/context/debt-registry.md": GENERATED_HEADER_MD + debt_registry_template(config),
        "templates/task-records/TASK-INDEX.md": GENERATED_HEADER_MD + task_index_template(config, date),
        "templates/task-records/task-record.md": GENERATED_HEADER_MD
        + task_record_content(config, task_args, "<changelog文件名>.md", timestamp),
        "templates/changelog/CHANGELOG-INDEX.md": GENERATED_HEADER_MD + changelog_index_template(config, date),
        "templates/changelog/changelog-entry.md": GENERATED_HEADER_MD
        + changelog_content(config, task_args, "<task文件名>.md", timestamp),
        "templates/plan-records/PLAN-INDEX.md": GENERATED_HEADER_MD + plan_index_template(config, date),
        "templates/plan-records/plan-record.md": GENERATED_HEADER_MD
        + plan_record_content(config, plan_args, timestamp),
        "templates/conversation-records/CONVERSATION-INDEX.md": GENERATED_HEADER_MD
        + conversation_index_template(config, date),
        "templates/conversation-records/conversation-record.md": GENERATED_HEADER_MD
        + conversation_record_content(config, conversation_args, timestamp),
        "adapters/README.md": GENERATED_NOTE,
        "adapters/claude-code/CLAUDE.md.snippet": marker_block(host_snippet(config)),
        "adapters/codex/AGENTS.md.snippet": marker_block(host_snippet(config)),
        "adapters/cursor/fengchao.mdc": cursor_rule(config),
        "adapters/opencode/opencode.json.snippet": opencode_config(config),
        "adapters/thin-skill-entry/SKILL.md": thin_skill_entry(config),
    }
    command_dirs = {"claude": "claude-code", "cursor": "cursor", "opencode": "opencode"}
    for agent, out_dir in command_dirs.items():
        for verb in COMMAND_VERBS:
            name = Path(AGENT_COMMAND_PATHS[agent].format(verb=verb)).name
            files[f"adapters/{out_dir}/commands/{name}"] = command_file_content(config, agent, verb)
    return files


def export_templates_project(project: Path, args: argparse.Namespace) -> int:
    out = Path(args.out)
    if not out.is_absolute():
        out = project / out
    files = generate_exported_templates()
    for rel, content in files.items():
        write_text(out / rel, content)
    print(f"exported {len(files)} files to {out}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# 参数解析与入口
# ---------------------------------------------------------------------------


def add_format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["text", "json"], default="text")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fengchao", description="Maintain FengChao project business memory artifacts."
    )
    parser.add_argument("--version", action="version", version=f"fengchao {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Initialize FengChao in a target project.")
    init.add_argument("--project-name", default=None)
    init.add_argument("--memory-root", default=DEFAULT_MEMORY_ROOT)
    init.add_argument("--agents", default="", help=f"逗号分隔：{','.join(AGENT_CHOICES)}；缺省时自动探测")
    init.add_argument("--memory-only", action="store_true", help="只创建记忆脚手架和 config，不装 skill、不写宿主注入")
    init.add_argument("--no-hooks", action="store_true", help="不向 .claude/settings.json 注册 hooks")
    init.add_argument("--hook-mode", choices=["remind", "strict", "off"], default="remind")
    init.add_argument("--language", choices=["zh-CN", "en"], default="zh-CN")
    init.set_defaults(func=init_project)

    maintain = subparsers.add_parser("maintain", help="Create records after real development delivery.")
    maintain.add_argument("--title", required=True)
    maintain.add_argument("--summary", required=True)
    maintain.add_argument("--implementation", required=True)
    maintain.add_argument("--business-change", default="")
    maintain.add_argument("--change-kind", choices=["added", "modified", "removed"], default="added")
    maintain.add_argument("--rule-name", default="")
    maintain.add_argument("--scenario", default="")
    maintain.add_argument("--with-task-record", action="store_true", help="lite 交付也强制写 task-record")
    maintain.add_argument("--decision", default="")
    maintain.add_argument("--risk", default="")
    maintain.add_argument("--domain", default="general")
    maintain.add_argument("--change-type", default="development")
    maintain.add_argument("--changed-file", action="append")
    maintain.add_argument("--evidence", action="append")
    maintain.add_argument("--validation", action="append")
    maintain.add_argument("--from-plan", action="append")
    maintain.add_argument("--from-conversation", action="append")
    add_format_argument(maintain)
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
    plan.add_argument("--status", default="proposed", choices=list(PLAN_STATUS_CHOICES))
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
    conversation.add_argument(
        "--confirmed-fact",
        action="append",
        default=[],
        metavar="名称=值",
        help="登记用户确凿断言的项目事实（可重复）；同名事实覆盖旧值，旧来源转入沿革",
    )
    conversation.add_argument(
        "--fact-kind",
        default=DEFAULT_FACT_KIND,
        help="本次事实的类别标签（自由文本，如 entry-point/config/term-anchor/convention）",
    )
    conversation.add_argument(
        "--retire-fact",
        action="append",
        default=[],
        metavar="名称",
        help="废除一条已失效的现行事实（可重复）",
    )
    add_format_argument(conversation)
    conversation.set_defaults(func=conversation_project)

    fengwang = subparsers.add_parser("fengwang", help="Route a user request to relevant memory files.")
    fengwang.add_argument("--query", required=True)
    fengwang.add_argument("--limit", type=int, default=12)
    fengwang.add_argument("--budget", type=int, default=DEFAULT_ROUTE_BUDGET_BYTES, help="输出字节预算")
    add_format_argument(fengwang)
    fengwang.set_defaults(func=fengwang_query)

    inspect = subparsers.add_parser("inspect", help="Inspect project files without mutating them.")
    inspect.add_argument("--limit", type=int, default=80)
    inspect.set_defaults(func=inspect_project)

    check = subparsers.add_parser("check", help="Validate FengChao artifacts and links.")
    check.add_argument("--require-records-for-git-changes", action="store_true")
    check.add_argument("--strict", action="store_true", help="现行为 + 要求 git 变更当天有 changelog（供 CI/hook strict）")
    check.add_argument("--warn", action="store_true", help="只打印问题，退出码恒为 0")
    add_format_argument(check)
    check.set_defaults(func=check_project)

    status = subparsers.add_parser("status", help="Show FengChao installation and memory health.")
    add_format_argument(status)
    status.set_defaults(func=status_project)

    enable = subparsers.add_parser("enable", help="Re-install host injections (inverse of disable).")
    enable.set_defaults(func=enable_project)

    disable = subparsers.add_parser("disable", help="Remove host injections; keep all memory and .fengchao/.")
    disable.set_defaults(func=disable_project)

    uninstall = subparsers.add_parser("uninstall", help="disable + remove .fengchao/; never touches memory by default.")
    uninstall.add_argument("--purge-memory", action="store_true", help="连记忆数据一起删除（需要二次确认）")
    uninstall.add_argument("--yes", action="store_true", help="跳过交互确认（供脚本使用）")
    uninstall.set_defaults(func=uninstall_project)

    hook = subparsers.add_parser("hook", help="Claude Code hook entrypoints (SessionStart/Stop).")
    hook.add_argument("event", choices=["session-start", "stop-gate"])
    hook.set_defaults(func=hook_project)

    git_hook = subparsers.add_parser("install-git-hook", help="Optional git pre-commit reminder hook.")
    git_hook.add_argument("--remove", action="store_true")
    git_hook.set_defaults(func=install_git_hook_project)

    migrate = subparsers.add_parser("migrate", help="Migrate legacy layout to the single memory root layout.")
    migrate.add_argument("--memory-root", default="")
    migrate.set_defaults(func=migrate_project)

    archive = subparsers.add_parser("archive", help="Move old records into archive/ subdirectories.")
    archive.add_argument("--before", required=True, help="归档早于该日期（YYYY-MM-DD）的记录")
    archive.set_defaults(func=archive_project)

    compact = subparsers.add_parser("compact", help="Rebuild memory-map: dedupe, reorder, fold archived rows.")
    compact.set_defaults(func=compact_project)

    plan_status = subparsers.add_parser("plan-status", help="Update a plan record's status and landing links.")
    plan_status.add_argument("record", help="plan 记录路径（相对项目根或记忆根）")
    plan_status.add_argument("--status", required=True, choices=list(PLAN_STATUS_CHOICES))
    plan_status.add_argument("--link", default="", help="落地后的 task-record 路径")
    plan_status.set_defaults(func=plan_status_project)

    doctor = subparsers.add_parser("doctor", help="Deep health check: legacy layout, orphans, dead rows.")
    add_format_argument(doctor)
    doctor.set_defaults(func=doctor_project)

    upgrade = subparsers.add_parser("upgrade", help="Rewrite tool artifacts with current CLI version; never touches memory.")
    upgrade.set_defaults(func=upgrade_project)

    export_templates = subparsers.add_parser(
        "export-templates", help="Generate templates/ and adapters/ from inline templates (dev command)."
    )
    export_templates.add_argument("--out", required=True)
    export_templates.set_defaults(func=export_templates_project)

    return parser


def main(argv: "list[str] | None" = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path(os.getcwd()).resolve()
    try:
        return args.func(project, args)
    except KeyboardInterrupt:
        print("cancelled", file=sys.stderr)
        return EXIT_CANCELLED


if __name__ == "__main__":
    raise SystemExit(main())
