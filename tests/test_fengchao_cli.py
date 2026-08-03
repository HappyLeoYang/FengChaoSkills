"""FengChao CLI 端到端测试。

延续项目约定：通过 subprocess 调真实 CLI、临时目录隔离、不 mock。
纯函数（路由打分、语义合并）另有直接 import 的单元测试类。
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "fengchao-business-memory" / "scripts" / "fengchao.py"

sys.path.insert(0, str(CLI.parent))
import fengchao  # noqa: E402  纯函数单测直接 import


def run_cli(cwd, *args, check=True, stdin_text=None, env=None):
    # 默认剥离 CLAUDE_PROJECT_DIR：在 Claude Code 会话内跑测试时，该变量指向本仓库
    # （仓库自身 dogfooding 有 .fengchao/），会让 hook 用例解析到仓库而非临时项目。
    proc_env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    if env:
        proc_env.update(env)
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=cwd,
        env=proc_env,
        text=True,
        input=stdin_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"fengchao {' '.join(args)} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def run_git(cwd, *args):
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def tree_digest(root: Path) -> str:
    """整棵目录树的内容指纹，用于逐字节还原断言。"""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def maintain_full(project, title, rule, kind, rule_name, domain="design", scenario="场景"):
    return run_cli(
        project,
        "maintain",
        "--title", title,
        "--summary", f"{title} 的业务诉求",
        "--implementation", f"{title} 的实现",
        "--business-change", rule,
        "--change-kind", kind,
        "--rule-name", rule_name,
        "--scenario", scenario,
        "--domain", domain,
    )


class InitLayoutTests(unittest.TestCase):
    def test_init_single_root_layout_and_thin_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            before_visible = {p.name for p in project.iterdir() if not p.name.startswith(".")}

            run_cli(project, "init", "--project-name", "Demo PDM")

            # A1 验收：新增顶层可见目录 ≤ 2（.fengchao 隐藏 + 记忆根 fengchao/）
            after_visible = {p.name for p in project.iterdir() if p.is_dir() and not p.name.startswith(".")}
            self.assertLessEqual(len(after_visible - before_visible), 2)
            self.assertIn("fengchao", after_visible)

            # skill 正文只存在一份（.fengchao/skill/），agent 目录只有薄入口
            self.assertTrue((project / ".fengchao" / "skill" / "SKILL.md").is_file())
            self.assertTrue((project / ".fengchao" / "skill" / "references" / "lifecycle.md").is_file())
            thin = (project / ".claude" / "skills" / "fengchao-business-memory" / "SKILL.md").read_text()
            self.assertIn(".fengchao/skill/SKILL.md", thin)
            self.assertLess(len(thin), 600)
            self.assertFalse(
                (project / ".claude" / "skills" / "fengchao-business-memory" / "references").exists()
            )

            # 记忆根：FENGWANG 上移到记忆根，一眼可见
            self.assertTrue((project / "fengchao" / "FENGWANG.md").is_file())
            self.assertTrue((project / "fengchao" / "memory-map.md").is_file())
            self.assertTrue((project / "fengchao" / "business-context" / "CONTEXT-INDEX.md").is_file())
            self.assertTrue((project / "fengchao" / "task-records" / "TASK-INDEX.md").is_file())

            # marker 块与薄命令（A3 / A4）
            claude_md = (project / "CLAUDE.md").read_text()
            self.assertIn("FENGCHAO-BUSINESS-MEMORY:START", claude_md)
            self.assertIn("FENGCHAO-BUSINESS-MEMORY:END", claude_md)
            self.assertTrue((project / ".claude" / "commands" / "fengchao" / "route.md").is_file())
            self.assertTrue((project / ".cursor" / "commands" / "fengchao-route.md").is_file())
            self.assertTrue((project / ".opencode" / "commands" / "fengchao-status.md").is_file())
            # Cursor 命令无 frontmatter（2026-07 核实的约定）
            cursor_cmd = (project / ".cursor" / "commands" / "fengchao-route.md").read_text()
            self.assertFalse(cursor_cmd.startswith("---"))

            # hooks 默认注册（B1）
            settings = json.loads((project / ".claude" / "settings.json").read_text())
            commands = [
                hook["command"]
                for entries in settings["hooks"].values()
                for entry in entries
                for hook in entry["hooks"]
            ]
            self.assertTrue(any("hook session-start" in c for c in commands))
            self.assertTrue(any("hook stop-gate" in c for c in commands))

            run_cli(project, "check")

    def test_init_preserves_existing_host_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "CLAUDE.md").write_text("# 用户自己的规则\n\n保持原样。\n")
            (project / "AGENTS.md").write_text("# 已有 agents 说明\n")
            (project / "opencode.json").write_text('{\n  "user": true\n}\n')

            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude,codex,opencode")

            claude_md = (project / "CLAUDE.md").read_text()
            self.assertTrue(claude_md.startswith("# 用户自己的规则\n\n保持原样。\n"))
            self.assertIn("FENGCHAO-BUSINESS-MEMORY:START", claude_md)
            self.assertIn("已有 agents 说明", (project / "AGENTS.md").read_text())
            # opencode.json 已存在时一字不动（A3）
            self.assertEqual('{\n  "user": true\n}\n', (project / "opencode.json").read_text())

    def test_init_agents_detection_and_explicit_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / ".cursor").mkdir()
            run_cli(project, "init", "--project-name", "Demo")
            # 探测到 .cursor → 只装 cursor surface
            self.assertTrue((project / ".cursor" / "rules" / "fengchao.mdc").is_file())
            self.assertFalse((project / "CLAUDE.md").exists())

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            self.assertTrue((project / "CLAUDE.md").exists())
            self.assertFalse((project / ".cursor" / "rules" / "fengchao.mdc").exists())
            self.assertFalse((project / "opencode.json").exists())

    def test_init_memory_only_writes_no_host_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--memory-only", "--project-name", "Demo")
            self.assertTrue((project / "fengchao" / "FENGWANG.md").is_file())
            self.assertTrue((project / ".fengchao" / "config.yaml").is_file())
            self.assertFalse((project / ".fengchao" / "skill").exists())
            self.assertFalse((project / "CLAUDE.md").exists())
            self.assertFalse((project / "AGENTS.md").exists())
            run_cli(project, "check")


class LifecycleTests(unittest.TestCase):
    def test_disable_enable_roundtrip_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "CLAUDE.md").write_text("# 用户内容\n")
            (project / ".cursor").mkdir()
            (project / ".claude").mkdir()
            run_cli(project, "init", "--project-name", "Demo")
            before = tree_digest(project)

            run_cli(project, "disable")
            self.assertNotIn("FENGCHAO", (project / "CLAUDE.md").read_text())
            self.assertFalse((project / ".cursor" / "rules" / "fengchao.mdc").exists())
            self.assertFalse((project / ".claude" / "settings.json").exists())
            # 记忆与工具本体保留
            self.assertTrue((project / "fengchao" / "FENGWANG.md").is_file())
            self.assertTrue((project / ".fengchao" / "skill" / "SKILL.md").is_file())

            run_cli(project, "enable")
            self.assertEqual(before, tree_digest(project))

    def test_uninstall_never_touches_memory_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            run_cli(project, "uninstall")
            self.assertFalse((project / ".fengchao").exists())
            self.assertFalse((project / "CLAUDE.md").exists())
            self.assertTrue((project / "fengchao" / "FENGWANG.md").is_file())

    def test_uninstall_purge_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            # 非 TTY 且无 --yes：拒绝并退出 130（附录 C）
            result = run_cli(project, "uninstall", "--purge-memory", check=False)
            self.assertEqual(130, result.returncode)
            self.assertTrue((project / "fengchao").exists())

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            run_cli(project, "uninstall", "--purge-memory", "--yes")
            self.assertFalse((project / "fengchao").exists())

    def test_status_json_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            result = run_cli(project, "status", "--format", "json")
            payload = json.loads(result.stdout)
            self.assertEqual("status", payload["command"])
            self.assertEqual("single-root", payload["layout"])
            self.assertTrue(payload["enabled"])
            self.assertIn("records", payload)


class MaintainTierTests(unittest.TestCase):
    def test_full_tier_creates_records_indexes_and_rule_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            maintain_full(
                project,
                "设计单两级审核",
                "设计单最终通过必须依次经过主管审核和经理审核。",
                "added",
                "设计单审核流程",
            )
            task_files = sorted((project / "fengchao" / "task-records").glob("20*_*.md"))
            changelog_files = sorted((project / "fengchao" / "changelog").glob("20*_*.md"))
            self.assertEqual(1, len(task_files))
            self.assertEqual(1, len(changelog_files))
            task_index = (project / "fengchao" / "task-records" / "TASK-INDEX.md").read_text()
            self.assertIn("设计单两级审核", task_index)
            domain_doc = (project / "fengchao" / "business-context" / "domains" / "domain-design.md").read_text()
            self.assertIn("### 规则：设计单审核流程", domain_doc)
            self.assertIn("设计单最终通过必须依次经过主管审核和经理审核。", domain_doc)
            memory_map = (project / "fengchao" / "memory-map.md").read_text()
            self.assertIn("task-records/", memory_map)
            self.assertIn("changelog/", memory_map)
            run_cli(project, "check")

    def test_full_tier_requires_rule_name_with_usage_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            result = run_cli(
                project,
                "maintain",
                "--title", "缺规则名",
                "--summary", "s",
                "--implementation", "i",
                "--business-change", "规则文本",
                check=False,
            )
            self.assertEqual(2, result.returncode)
            self.assertIn("--rule-name", result.stderr)

    def test_lite_tier_writes_changelog_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            result = run_cli(
                project,
                "maintain",
                "--title", "修复空指针",
                "--summary", "审核页报错",
                "--implementation", "补空值判断",
                "--domain", "design",
            )
            self.assertIn("tier: lite", result.stdout)
            self.assertEqual(0, len(list((project / "fengchao" / "task-records").glob("20*_*.md"))))
            changelog_files = sorted((project / "fengchao" / "changelog").glob("20*_*.md"))
            self.assertEqual(1, len(changelog_files))
            self.assertIn("lite 交付", changelog_files[0].read_text())
            # 不动 business-context
            self.assertFalse(
                (project / "fengchao" / "business-context" / "domains" / "domain-design.md").exists()
            )
            run_cli(project, "check")

    def test_lite_tier_with_task_record_escape_hatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            run_cli(
                project,
                "maintain",
                "--title", "重大重构",
                "--summary", "s",
                "--implementation", "i",
                "--with-task-record",
            )
            self.assertEqual(1, len(list((project / "fengchao" / "task-records").glob("20*_*.md"))))


class DeltaMergeTests(unittest.TestCase):
    """B4 验收标准：added → modified → modified 始终只有一个现行条目，沿革可追。"""

    def test_added_modified_modified_keeps_single_active_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            maintain_full(project, "两级审核", "两级审核规则。", "added", "设计单审核流程")
            maintain_full(project, "三级审核", "三级审核规则。", "modified", "设计单审核流程")
            maintain_full(project, "回到两级", "回退为两级审核规则。", "modified", "设计单审核流程")

            domain_doc = (project / "fengchao" / "business-context" / "domains" / "domain-design.md").read_text()
            self.assertEqual(1, domain_doc.count("### 规则：设计单审核流程"))
            self.assertIn("回退为两级审核规则。", domain_doc)
            self.assertNotIn("- **规则**：两级审核规则。", domain_doc)
            # 沿革链：两任旧版本的 task-record 链接都在
            history_line = next(
                line for line in domain_doc.splitlines() if line.startswith("- **沿革**")
            )
            self.assertIn("三级审核", history_line)
            self.assertIn("两级审核", history_line)
            run_cli(project, "check")

    def test_removed_moves_rule_to_retired_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            maintain_full(project, "加急通道", "设计单支持加急通道。", "added", "设计单加急通道")
            maintain_full(project, "取消加急通道", "废除加急通道。", "removed", "设计单加急通道")
            domain_doc = (project / "fengchao" / "business-context" / "domains" / "domain-design.md").read_text()
            self.assertNotIn("### 规则：设计单加急通道", domain_doc)
            self.assertIn("~~设计单加急通道~~", domain_doc)
            run_cli(project, "check")

    def test_wrong_change_kind_fails_whole_without_partial_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            maintain_full(project, "两级审核", "两级审核规则。", "added", "设计单审核流程")
            records_before = sorted((project / "fengchao" / "task-records").glob("20*_*.md"))

            # added 重名 → rule_already_exists
            result = maintain_full_noncheck = run_cli(
                project, "maintain",
                "--title", "重复", "--summary", "s", "--implementation", "i",
                "--business-change", "x", "--change-kind", "added",
                "--rule-name", "设计单审核流程", "--domain", "design",
                "--format", "json",
                check=False,
            )
            self.assertEqual(1, result.returncode)
            payload = json.loads(result.stdout)
            self.assertEqual("error", payload["status"])
            self.assertEqual("rule_already_exists", payload["diagnostics"][0]["code"])
            self.assertIn("fix", payload["diagnostics"][0])

            # modified 不存在 → rule_not_found + 最相近候选
            result = run_cli(
                project, "maintain",
                "--title", "改错名", "--summary", "s", "--implementation", "i",
                "--business-change", "x", "--change-kind", "modified",
                "--rule-name", "设计单审批流程", "--domain", "design",
                check=False,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("rule_not_found", result.stderr)
            self.assertIn("设计单审核流程", result.stderr)

            # 失败即整体失败：没有半成品 task/changelog
            records_after = sorted((project / "fengchao" / "task-records").glob("20*_*.md"))
            self.assertEqual(records_before, records_after)
            run_cli(project, "check")


class CheckContractTests(unittest.TestCase):
    def test_check_reports_broken_link_with_json_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            task_index = project / "fengchao" / "task-records" / "TASK-INDEX.md"
            task_index.write_text(
                task_index.read_text() + "\n- [missing](2026-05-11_001_missing.md)\n"
            )
            result = run_cli(project, "check", check=False)
            self.assertEqual(1, result.returncode)
            self.assertIn("broken_link", result.stderr)

            result = run_cli(project, "check", "--format", "json", check=False)
            self.assertEqual(1, result.returncode)
            payload = json.loads(result.stdout)
            self.assertEqual("error", payload["status"])
            self.assertEqual("check", payload["command"])
            codes = {d["code"] for d in payload["diagnostics"]}
            self.assertIn("broken_link", codes)

            # --warn：只打印问题，退出码恒为 0（B2）
            result = run_cli(project, "check", "--warn", check=False)
            self.assertEqual(0, result.returncode)

    def test_check_strict_requires_changelog_for_git_changes_lite_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_git(project, "init")
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            (project / "app.py").write_text("print('hi')\n")

            result = run_cli(project, "check", "--strict", check=False)
            self.assertEqual(1, result.returncode)
            self.assertIn("missing_changelog_for_changes", result.stderr)

            # lite 交付只写 changelog，strict 不误报（B5 验收）
            run_cli(
                project, "maintain",
                "--title", "修复", "--summary", "s", "--implementation", "i",
            )
            run_cli(project, "check", "--strict")


class FengwangRoutingTests(unittest.TestCase):
    def test_routing_ranks_matching_records_and_respects_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            maintain_full(project, "设计单两级审核", "两级审核。", "added", "设计单审核流程")
            run_cli(
                project, "maintain",
                "--title", "订单导出优化", "--summary", "订单列表导出加速",
                "--implementation", "分页导出", "--domain", "order",
            )
            result = run_cli(project, "fengwang", "--query", "设计单审核")
            lines = [l for l in result.stdout.splitlines() if l and l[0].isdigit()]
            self.assertTrue(lines)
            self.assertIn("设计单两级审核", lines[0])
            self.assertNotIn("订单导出", lines[0])

            # 预算截断（C1）：极小预算下输出行数受限且明示截断
            result = run_cli(project, "fengwang", "--query", "设计单审核", "--budget", "300")
            self.assertIn("已截断", result.stdout)

            result = run_cli(project, "fengwang", "--query", "设计单审核", "--format", "json")
            payload = json.loads(result.stdout)
            self.assertEqual("fengwang", payload["command"])
            self.assertTrue(payload["results"])
            self.assertIn("target", payload["results"][0])


class ScoringUnitTests(unittest.TestCase):
    """C1：打分纯函数单测（100+ 行 memory-map，Top-3 命中率优于 v1 子串匹配）。"""

    def _rows(self):
        rows = []
        for idx in range(100):
            rows.append(
                fengchao.MemoryRow(
                    record_type="changelog",
                    status="historical",
                    domain="misc",
                    keywords=f"任务 变更 常规 杂项 编号{idx}",
                    link_label=f"2026-01-01_{idx:03d}_noise.md",
                    link_target=f"changelog/2026-01-01_{idx:03d}_noise.md",
                    description="已落地变更记录",
                    date="2026-01-01",
                    raw="",
                )
            )
        rows.append(
            fengchao.MemoryRow(
                record_type="task",
                status="implemented",
                domain="design",
                keywords="设计单 审核 主管 经理 两级",
                link_label="2026-07-01_001_review.md",
                link_target="task-records/2026-07-01_001_review.md",
                description="设计单审核任务",
                date="2026-07-01",
                raw="",
            )
        )
        rows.append(
            fengchao.MemoryRow(
                record_type="context",
                status="current",
                domain="design",
                keywords="设计 上下文",
                link_label="CONTEXT-INDEX.md",
                link_target="business-context/CONTEXT-INDEX.md",
                description="当前业务上下文入口",
                date="",
                raw="",
            )
        )
        return rows

    def test_rare_terms_outweigh_frequent_terms(self):
        rows = self._rows()
        scored = fengchao.score_memory_rows("设计单审核怎么改", rows, reference_date="2026-07-09")
        top3 = [row.link_target for _, row in scored[:3]]
        self.assertIn("task-records/2026-07-01_001_review.md", top3)
        # 高频词"任务/变更"不应把噪音行顶进 Top-3
        self.assertNotIn("noise", top3[0])

    def test_context_type_and_domain_bonus(self):
        rows = self._rows()
        scored = fengchao.score_memory_rows("design 设计", rows, reference_date="2026-07-09")
        self.assertTrue(scored)
        self.assertEqual("context", scored[0][1].record_type)

    def test_tokenizer_cjk_bigrams(self):
        tokens = fengchao.tokenize_for_scoring("设计单审核 review-flow")
        self.assertIn("设计", tokens)
        self.assertIn("计单", tokens)
        self.assertIn("review", tokens)

    def test_collect_keywords_caps_length(self):
        keywords = fengchao.collect_keywords("很长的标题 " * 40, "内容 " * 60)
        self.assertLessEqual(len(keywords), fengchao.KEYWORDS_MAX_CHARS)


class HookTests(unittest.TestCase):
    def test_stop_gate_remind_once_per_session_and_ignores_memory_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_git(project, "init")
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            (project / "app.py").write_text("x = 1\n")

            payload = json.dumps({"session_id": "s1"})
            result = run_cli(project, "hook", "stop-gate", stdin_text=payload)
            self.assertIn("maintain", result.stdout)
            # 同会话第二次静默（防打扰）
            result = run_cli(project, "hook", "stop-gate", stdin_text=payload)
            self.assertEqual("", result.stdout.strip())

            # 纯记忆目录变更不触发
            run_git(project, "add", "-A")
            run_git(project, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init")
            (project / "fengchao" / "memory-map.md").open("a").write("| x |\n")
            result = run_cli(project, "hook", "stop-gate", stdin_text=json.dumps({"session_id": "s2"}))
            self.assertEqual("", result.stdout.strip())

    def test_stop_gate_strict_blocks_with_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_git(project, "init")
            run_cli(
                project, "init", "--project-name", "Demo", "--agents", "claude",
                "--hook-mode", "strict",
            )
            (project / "app.py").write_text("x = 1\n")
            result = run_cli(project, "hook", "stop-gate", stdin_text=json.dumps({"session_id": "s1"}))
            payload = json.loads(result.stdout)
            self.assertEqual("block", payload["decision"])
            self.assertIn("maintain", payload["reason"])

    def test_session_start_outputs_additional_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            result = run_cli(project, "hook", "session-start", stdin_text="{}")
            payload = json.loads(result.stdout)
            self.assertIn("FENGWANG.md", payload["hookSpecificOutput"]["additionalContext"])

    def test_hook_command_registered_with_project_dir_variable(self):
        """F-005：settings.json 中的 hook 命令用 $CLAUDE_PROJECT_DIR 锚定项目根。"""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            settings = json.loads((project / ".claude" / "settings.json").read_text())
            for event, sub in (("SessionStart", "session-start"), ("Stop", "stop-gate")):
                commands = [
                    hook["command"]
                    for entry in settings["hooks"][event]
                    for hook in entry.get("hooks", [])
                    if "fengchao" in str(hook.get("command", ""))
                ]
                self.assertEqual(commands, [fengchao.HOOK_COMMAND_PREFIX + sub])
                self.assertIn("${CLAUDE_PROJECT_DIR:-.}", commands[0])

    def test_session_start_resolves_root_from_env_in_subdir(self):
        """F-005：cwd 在子目录时经 $CLAUDE_PROJECT_DIR 解析项目根，注入命令为绝对路径。"""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            subdir = project / "spikes" / "deep"
            subdir.mkdir(parents=True)
            result = run_cli(
                subdir, "hook", "session-start", stdin_text="{}",
                env={"CLAUDE_PROJECT_DIR": str(project)},
            )
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("FENGWANG.md", context)
            # maintain 命令是绝对路径，AI 在任意 cwd 照抄可执行
            self.assertIn(str(project.resolve() / fengchao.CLI_RELATIVE), context)

    def test_stop_gate_walks_up_from_subdir_without_env(self):
        """F-005：无环境变量时从 cwd 向上 walk-up 定位项目根，防重标记跨 cwd 共享。"""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_git(project, "init")
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            (project / "app.py").write_text("x = 1\n")
            subdir = project / "spikes" / "spike2_engine"
            subdir.mkdir(parents=True)
            payload = json.dumps({"session_id": "s1"})
            result = run_cli(subdir, "hook", "stop-gate", stdin_text=payload)
            self.assertIn("maintain", result.stdout)
            self.assertTrue((project / ".fengchao" / "tmp" / "stop-gate-s1").exists())
            # 同会话换回项目根执行，防重标记命中，不再提醒
            result = run_cli(project, "hook", "stop-gate", stdin_text=payload)
            self.assertEqual("", result.stdout.strip())

    def test_hook_outside_any_project_is_silent(self):
        """F-005 回归：未初始化环境里 hook 保持静默空跑（rc=0、零输出）。"""
        with tempfile.TemporaryDirectory() as tmp:
            subdir = Path(tmp) / "nested" / "dir"
            subdir.mkdir(parents=True)
            for event in ("session-start", "stop-gate"):
                result = run_cli(subdir, "hook", event, stdin_text="{}")
                self.assertEqual(0, result.returncode)
                self.assertEqual("", result.stdout.strip())


class HookUpgradeCompatTests(unittest.TestCase):
    """v0.2.0 旧格式 hook 的升级替换与卸载对称性（F-005 LEGACY 清单，红线 6）。"""

    @staticmethod
    def _legacy_command(sub: str) -> str:
        return f"python3 {fengchao.CLI_RELATIVE} hook {sub}"

    def test_upgrade_replaces_legacy_hook_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            settings_path = project / ".claude" / "settings.json"
            legacy = {
                "hooks": {
                    "SessionStart": [
                        {"hooks": [{"type": "command", "command": self._legacy_command("session-start"), "timeout": 10}]}
                    ],
                    "Stop": [
                        {"hooks": [{"type": "command", "command": self._legacy_command("stop-gate"), "timeout": 10}]},
                        {"hooks": [{"type": "command", "command": "echo hi"}]},
                    ],
                }
            }
            settings_path.write_text(json.dumps(legacy, ensure_ascii=False, indent=2) + "\n")
            run_cli(project, "upgrade")
            text = settings_path.read_text()
            self.assertNotIn(f"python3 {fengchao.CLI_RELATIVE} hook ", text)
            data = json.loads(text)
            for event, sub in (("SessionStart", "session-start"), ("Stop", "stop-gate")):
                ours = [
                    hook["command"]
                    for entry in data["hooks"][event]
                    for hook in entry.get("hooks", [])
                    if "fengchao" in str(hook.get("command", ""))
                ]
                # 旧条目被替换而非追加：恰好一条新格式
                self.assertEqual(ours, [fengchao.HOOK_COMMAND_PREFIX + sub])
            user_hooks = [
                hook["command"]
                for entry in data["hooks"]["Stop"]
                for hook in entry.get("hooks", [])
                if hook.get("command") == "echo hi"
            ]
            self.assertEqual(["echo hi"], user_hooks)

    def test_disable_removes_legacy_format_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            settings_path = project / ".claude" / "settings.json"
            legacy_only = {
                "hooks": {
                    "Stop": [
                        {"hooks": [{"type": "command", "command": self._legacy_command("stop-gate"), "timeout": 10}]}
                    ]
                }
            }
            settings_path.write_text(json.dumps(legacy_only, ensure_ascii=False, indent=2) + "\n")
            run_cli(project, "disable")
            # 全部条目都是我们的 → 摘除后走 unlink 分支，文件消失
            self.assertFalse(settings_path.exists())


class ScaleLifecycleTests(unittest.TestCase):
    def test_archive_moves_records_and_keeps_links_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            maintain_full(project, "两级审核", "两级审核。", "added", "设计单审核流程")
            run_cli(project, "archive", "--before", "2099-01-01")
            archived = list((project / "fengchao" / "task-records" / "archive").glob("20*_*.md"))
            self.assertEqual(1, len(archived))
            self.assertIn("archive/", (project / "fengchao" / "memory-map.md").read_text())
            run_cli(project, "check")

    def test_compact_dedupes_and_folds_archived_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            maintain_full(project, "两级审核", "两级审核。", "added", "设计单审核流程")
            memory_map = project / "fengchao" / "memory-map.md"
            rows = [l for l in memory_map.read_text().splitlines() if "task-records/20" in l]
            memory_map.write_text(memory_map.read_text() + rows[0] + "\n")  # 制造重复行
            run_cli(project, "archive", "--before", "2099-01-01")
            result = run_cli(project, "compact")
            self.assertIn("duplicates removed", result.stdout)
            self.assertIn("已归档记录", memory_map.read_text())
            run_cli(project, "check")

    def test_plan_status_backfills_links_and_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            run_cli(
                project, "plan",
                "--title", "审核优化计划", "--goal", "g", "--plan", "p", "--domain", "design",
            )
            maintain_full(project, "审核优化落地", "两级审核。", "added", "设计单审核流程")
            plan_file = sorted((project / "fengchao" / "plan-records").glob("20*_*.md"))[0]
            task_file = sorted((project / "fengchao" / "task-records").glob("20*_*.md"))[0]
            run_cli(
                project, "plan-status",
                str(plan_file.relative_to(project)),
                "--status", "implemented",
                "--link", str(task_file.relative_to(project)),
            )
            plan_text = plan_file.read_text()
            self.assertIn("**计划状态**：implemented", plan_text)
            self.assertIn(task_file.name, plan_text)
            self.assertIn("`implemented`", (project / "fengchao" / "plan-records" / "PLAN-INDEX.md").read_text())
            run_cli(project, "check")

    def test_doctor_detects_orphans_and_legacy_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            (project / "fengchao" / "task-records" / "2026-01-01_001_orphan.md").write_text("# 孤儿\n")
            domain = project / "fengchao" / "business-context" / "domains" / "domain-general.md"
            domain.write_text(domain.read_text() + "\n## 2026-01-01 已落地业务事实\n\n- 旧条目\n")
            result = run_cli(project, "doctor")
            self.assertIn("orphan_record", result.stdout)
            self.assertIn("legacy_context_entry", result.stdout)
            self.assertEqual(0, result.returncode)


class MigrateUpgradeTests(unittest.TestCase):
    def _build_legacy_project(self, project: Path):
        """手工构造最小老布局项目（六目录散根下 + 老式 config）。"""
        (project / ".fengchao").mkdir()
        (project / ".fengchao" / "config.yaml").write_text(
            '# legacy\nproject_name: "Legacy"\ncontext_dir: "business-context"\n'
            'task_dir: "task-records"\nchangelog_dir: "changelog"\nplan_dir: "plan-records"\n'
            'conversation_dir: "conversation-records"\nfengwang_dir: "fengwang"\n'
        )
        for name in ("task-records", "changelog", "plan-records", "conversation-records"):
            (project / name).mkdir()
        (project / "business-context" / "domains").mkdir(parents=True)
        (project / "fengwang").mkdir()
        (project / "business-context" / "CONTEXT-INDEX.md").write_text(
            "# 入口\n\n1. 读 `../fengwang/FENGWANG.md`。\n"
        )
        (project / "task-records" / "TASK-INDEX.md").write_text(
            "# 任务索引\n\n| 2026-01-01 | [t](2026-01-01_001_t.md) |\n"
        )
        (project / "task-records" / "2026-01-01_001_t.md").write_text("# 旧任务\n")
        (project / "changelog" / "CHANGELOG-INDEX.md").write_text("# changelog\n")
        (project / "plan-records" / "PLAN-INDEX.md").write_text("# plan\n")
        (project / "conversation-records" / "CONVERSATION-INDEX.md").write_text("# conv\n")
        (project / "fengwang" / "FENGWANG.md").write_text(
            "# 蜂王\n\n读 `../business-context/`。\n\n项目文档参考 `../docs/`。\n"
        )
        # memory-map 同时含指向记忆内部与记忆根之外（../docs/）的链接（F-003 场景）
        (project / "docs").mkdir()
        (project / "docs" / "业务文档.md").write_text("# 外部业务文档\n")
        (project / "fengwang" / "memory-map.md").write_text(
            "# Map\n\n| 类型 | 状态 | 领域 | 词 | 优先读取 | 说明 |\n|--|--|--|--|--|--|\n"
            "| task | implemented | general | 任务 | [2026-01-01_001_t.md](../task-records/2026-01-01_001_t.md) | 旧任务 |\n"
            "| doc | current | general | 文档 | [业务文档.md](../docs/业务文档.md) | 记忆根外的项目文档 |\n"
        )

    def test_migrate_legacy_to_single_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self._build_legacy_project(project)
            result = run_cli(project, "status")
            self.assertIn("legacy", result.stdout)

            run_cli(project, "migrate")
            self.assertTrue((project / "fengchao" / "FENGWANG.md").is_file())
            self.assertTrue((project / "fengchao" / "task-records" / "2026-01-01_001_t.md").is_file())
            self.assertFalse((project / "fengwang").exists())
            memory_map = (project / "fengchao" / "memory-map.md").read_text()
            # 内部链接剥掉 ../（上移一层后同级）
            self.assertIn("](task-records/2026-01-01_001_t.md)", memory_map)
            # F-003：记忆根外链接的 ../ 原样保留（check 对根外断链静默跳过，必须比对内容）
            self.assertIn("](../docs/业务文档.md)", memory_map)
            fengwang_text = (project / "fengchao" / "FENGWANG.md").read_text()
            self.assertIn("`business-context/`", fengwang_text)
            self.assertIn("`../docs/`", fengwang_text)
            run_cli(project, "check")

    def test_upgrade_rewrites_tool_but_not_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--agents", "claude")
            maintain_full(project, "两级审核", "两级审核。", "added", "设计单审核流程")
            task_file = sorted((project / "fengchao" / "task-records").glob("20*_*.md"))[0]
            memory_before = task_file.read_text()
            # 篡改 skill 副本 + 伪造旧版本号
            (project / ".fengchao" / "skill" / "SKILL.md").write_text("已被篡改\n")
            config = project / ".fengchao" / "config.yaml"
            config.write_text(config.read_text().replace(
                f'installed_version: "{fengchao.__version__}"', 'installed_version: "0.0.1"'
            ))
            result = run_cli(project, "status")
            self.assertIn("version_drift", result.stdout)

            result = run_cli(project, "upgrade")
            self.assertIn(fengchao.__version__, result.stdout)
            self.assertNotIn("已被篡改", (project / ".fengchao" / "skill" / "SKILL.md").read_text())
            self.assertEqual(memory_before, task_file.read_text())


class TemplateExportTests(unittest.TestCase):
    def test_export_templates_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "export-templates", "--out", "out1")
            run_cli(project, "export-templates", "--out", "out2")
            self.assertEqual(tree_digest(project / "out1"), tree_digest(project / "out2"))
            self.assertTrue((project / "out1" / "templates" / "fengwang" / "FENGWANG.md").is_file())
            self.assertTrue((project / "out1" / "adapters" / "cursor" / "fengchao.mdc").is_file())
            self.assertIn(
                "勿手改",
                (project / "out1" / "templates" / "context" / "domain.md").read_text(),
            )

    def test_repo_templates_match_inline_source(self):
        """D1：仓库内 templates/ 与 adapters/ 必须与内联模板一致（CI 同款校验）。"""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "export-templates", "--out", "exported")
            exported = project / "exported"
            for rel in sorted(
                p.relative_to(exported) for p in exported.rglob("*") if p.is_file()
            ):
                repo_file = ROOT / rel
                self.assertTrue(repo_file.is_file(), f"missing in repo: {rel}")
                self.assertEqual(
                    (exported / rel).read_text(),
                    repo_file.read_text(),
                    f"drift between inline template and repo copy: {rel}",
                )


class EnglishTemplateTests(unittest.TestCase):
    def test_en_init_and_full_maintain(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--language", "en", "--memory-only")
            fengwang_doc = (project / "fengchao" / "FENGWANG.md").read_text()
            self.assertIn("FengWang Routing Entry", fengwang_doc)
            run_cli(
                project, "maintain",
                "--title", "Two-level review",
                "--summary", "Need two-level review",
                "--implementation", "Add manager stage",
                "--business-change", "Design orders require two-level review.",
                "--change-kind", "added",
                "--rule-name", "Design review flow",
                "--scenario", "Supervisor first, then manager",
                "--domain", "design",
            )
            domain_doc = (project / "fengchao" / "business-context" / "domains" / "domain-design.md").read_text()
            self.assertIn("### Rule: Design review flow", domain_doc)
            self.assertIn("## Current Business Rules", domain_doc)
            run_cli(project, "check")


class PlanConversationTests(unittest.TestCase):
    def test_plan_and_conversation_do_not_touch_business_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            run_cli(
                project, "conversation",
                "--title", "审核角色业务解释", "--domain", "design",
                "--summary", "用户解释主管和经理审核的业务边界。",
                "--term", "主管=main 岗位，负责一审",
                "--rejected", "不继续使用 userId <= 100 判断管理员",
            )
            run_cli(
                project, "plan",
                "--title", "审核流程优化计划", "--domain", "design",
                "--goal", "用户希望调整审核流程。", "--plan", "拆成两级。",
            )
            domain_doc = (project / "fengchao" / "business-context" / "domains" / "domain-general.md").read_text()
            self.assertNotIn("主管=main 岗位", domain_doc)
            memory_map = (project / "fengchao" / "memory-map.md").read_text()
            self.assertIn("conversation", memory_map)
            self.assertIn("plan", memory_map)
            route = run_cli(project, "fengwang", "--query", "我要改设计单审核")
            self.assertIn("conversation-records/", route.stdout)
            run_cli(project, "check")


class GitHookTests(unittest.TestCase):
    def test_install_and_remove_pre_commit_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run_git(project, "init")
            run_cli(project, "init", "--project-name", "Demo", "--memory-only")
            run_cli(project, "install-git-hook")
            hook = project / ".git" / "hooks" / "pre-commit"
            self.assertTrue(hook.is_file())
            self.assertIn("FENGCHAO-BUSINESS-MEMORY", hook.read_text())
            run_cli(project, "install-git-hook", "--remove")
            self.assertFalse(hook.exists())


if __name__ == "__main__":
    unittest.main()
