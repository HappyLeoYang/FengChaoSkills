import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "fengchao-business-memory" / "scripts" / "fengchao.py"


class FengChaoCliTests(unittest.TestCase):
    def run_cli(self, cwd, *args, check=True):
        result = subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if check and result.returncode != 0:
            self.fail(
                f"fengchao {' '.join(args)} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        return result

    def test_init_creates_project_memory_artifacts_and_adapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)

            self.run_cli(project, "init", "--project-name", "Demo PDM")

            self.assertTrue((project / ".fengchao" / "config.yaml").is_file())
            self.assertTrue((project / "business-context" / "CONTEXT-INDEX.md").is_file())
            self.assertTrue((project / "fengwang" / "FENGWANG.md").is_file())
            self.assertTrue((project / "fengwang" / "memory-map.md").is_file())
            self.assertTrue((project / "plan-records" / "PLAN-INDEX.md").is_file())
            self.assertTrue((project / "conversation-records" / "CONVERSATION-INDEX.md").is_file())
            self.assertTrue((project / "task-records" / "TASK-INDEX.md").is_file())
            self.assertTrue((project / "changelog" / "CHANGELOG-INDEX.md").is_file())
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertTrue((project / ".cursor" / "rules" / "fengchao.mdc").is_file())
            self.assertTrue((project / "CLAUDE.md").is_file())
            self.assertTrue((project / "opencode.json").is_file())
            self.assertTrue(
                (project / ".opencode" / "skills" / "fengchao-business-memory" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (project / ".claude" / "skills" / "fengchao-business-memory" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (project / ".cursor" / "skills" / "fengchao-business-memory" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (project / ".codex" / "skills" / "fengchao-business-memory" / "SKILL.md").is_file()
            )
            self.assertTrue(
                (project / ".agents" / "skills" / "fengchao-business-memory" / "SKILL.md").is_file()
            )

            context_index = (project / "business-context" / "CONTEXT-INDEX.md").read_text()
            agents = (project / "AGENTS.md").read_text()
            claude = (project / "CLAUDE.md").read_text()
            cursor = (project / ".cursor" / "rules" / "fengchao.mdc").read_text()
            opencode = (project / "opencode.json").read_text()
            self.assertIn("Demo PDM", context_index)
            self.assertIn("渐进式上下文入口", context_index)
            self.assertIn("新会话先读取 `fengwang/FENGWANG.md`", agents)
            self.assertIn(".codex/skills/fengchao-business-memory/SKILL.md", agents)
            self.assertIn(".agents/skills/fengchao-business-memory/SKILL.md", agents)
            self.assertIn(".claude/skills/fengchao-business-memory/SKILL.md", claude)
            self.assertIn(".cursor/skills/fengchao-business-memory/SKILL.md", cursor)
            self.assertIn(".opencode/skills/fengchao-business-memory/scripts/fengchao.py check", agents)
            self.assertIn("fengwang/*.md", opencode)
            self.assertIn("plan-records/PLAN-INDEX.md", opencode)
            self.assertIn("conversation-records/CONVERSATION-INDEX.md", opencode)

    def test_maintain_creates_task_record_changelog_and_updates_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.run_cli(project, "init", "--project-name", "Demo")

            self.run_cli(
                project,
                "maintain",
                "--title",
                "设计单两级审核",
                "--summary",
                "用户要求把设计单审核从单级改成主管和经理两级。",
                "--business-change",
                "设计单最终通过必须经过主管审核和经理审核。",
                "--implementation",
                "新增审核阶段字段并调整审核状态机。",
                "--evidence",
                "PdmWorkOrderServiceImpl review flow",
                "--validation",
                "mvn compile passed",
                "--domain",
                "design",
                "--changed-file",
                "src/work-order.java",
            )

            task_files = sorted((project / "task-records").glob("20*_*.md"))
            changelog_files = sorted((project / "changelog").glob("20*_*.md"))
            self.assertEqual(1, len(task_files))
            self.assertEqual(1, len(changelog_files))

            task_index = (project / "task-records" / "TASK-INDEX.md").read_text()
            changelog_index = (project / "changelog" / "CHANGELOG-INDEX.md").read_text()
            domain_doc = (project / "business-context" / "domains" / "domain-design.md").read_text()

            self.assertIn("设计单两级审核", task_index)
            self.assertIn("design", task_index)
            self.assertIn("设计单两级审核", changelog_index)
            self.assertIn("设计单最终通过必须经过主管审核和经理审核。", domain_doc)

    def test_check_fails_when_index_links_missing_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.run_cli(project, "init", "--project-name", "Demo")
            task_index = project / "task-records" / "TASK-INDEX.md"
            task_index.write_text(
                task_index.read_text()
                + "\n- 2026-05-11 | missing | [missing](2026-05-11_001_missing.md)\n"
            )

            result = self.run_cli(project, "check", check=False)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("Broken link", result.stderr)

    def test_plan_and_conversation_update_indexes_and_fengwang_without_context_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.run_cli(project, "init", "--project-name", "Demo")

            self.run_cli(
                project,
                "conversation",
                "--title",
                "审核角色业务解释",
                "--domain",
                "design",
                "--summary",
                "用户解释主管和经理审核的业务边界。",
                "--term",
                "主管=main 岗位，负责一审",
                "--preference",
                "后端返回按钮权限，不让前端自行判断",
                "--rejected",
                "不继续使用 userId <= 100 判断管理员",
                "--promote",
                "no",
            )
            self.run_cli(
                project,
                "plan",
                "--title",
                "审核流程优化计划",
                "--domain",
                "design",
                "--goal",
                "用户希望调整审核流程。",
                "--plan",
                "把审核拆成主管和经理两级。",
                "--assumption",
                "主管对应 main 岗位。",
                "--open-question",
                "是否需要迁移历史数据。",
                "--status",
                "proposed",
            )

            conversation_files = sorted((project / "conversation-records").glob("20*_*.md"))
            plan_files = sorted((project / "plan-records").glob("20*_*.md"))
            self.assertEqual(1, len(conversation_files))
            self.assertEqual(1, len(plan_files))

            conversation_index = (project / "conversation-records" / "CONVERSATION-INDEX.md").read_text()
            plan_index = (project / "plan-records" / "PLAN-INDEX.md").read_text()
            memory_map = (project / "fengwang" / "memory-map.md").read_text()
            domain_doc = (project / "business-context" / "domains" / "domain-general.md").read_text()

            self.assertIn("审核角色业务解释", conversation_index)
            self.assertIn("审核流程优化计划", plan_index)
            self.assertIn("conversation", memory_map)
            self.assertIn("plan", memory_map)
            self.assertIn("主管", memory_map)
            self.assertNotIn("主管=main 岗位", domain_doc)

    def test_fengwang_query_and_maintain_links_plan_and_conversation(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.run_cli(project, "init", "--project-name", "Demo")

            self.run_cli(
                project,
                "conversation",
                "--title",
                "审核角色业务解释",
                "--domain",
                "design",
                "--summary",
                "用户解释主管和经理审核的业务边界。",
                "--term",
                "主管=main 岗位，负责一审",
            )
            self.run_cli(
                project,
                "plan",
                "--title",
                "审核流程优化计划",
                "--domain",
                "design",
                "--goal",
                "用户希望调整审核流程。",
                "--plan",
                "把审核拆成主管和经理两级。",
                "--status",
                "approved",
            )

            route = self.run_cli(project, "fengwang", "--query", "我要改设计单审核")
            self.assertIn("FengWang suggested context", route.stdout)
            self.assertIn("conversation-records/", route.stdout)
            self.assertIn("plan-records/", route.stdout)

            plan_file = sorted((project / "plan-records").glob("20*_*.md"))[0]
            conversation_file = sorted((project / "conversation-records").glob("20*_*.md"))[0]
            self.run_cli(
                project,
                "maintain",
                "--title",
                "设计单两级审核落地",
                "--summary",
                "用户要求把设计单审核从单级改成主管和经理两级。",
                "--business-change",
                "设计单最终通过必须经过主管审核和经理审核。",
                "--implementation",
                "新增审核阶段字段并调整审核状态机。",
                "--domain",
                "design",
                "--from-plan",
                str(plan_file.relative_to(project)),
                "--from-conversation",
                str(conversation_file.relative_to(project)),
            )

            task_file = sorted((project / "task-records").glob("20*_*.md"))[0]
            task_text = task_file.read_text()
            memory_map = (project / "fengwang" / "memory-map.md").read_text()
            self.assertIn(str(plan_file.relative_to(project)), task_text)
            self.assertIn(str(conversation_file.relative_to(project)), task_text)
            self.assertIn("task", memory_map)
            self.assertIn("changelog", memory_map)
            self.run_cli(project, "check")

    def test_check_fails_for_missing_conversation_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.run_cli(project, "init", "--project-name", "Demo")
            conversation_index = project / "conversation-records" / "CONVERSATION-INDEX.md"
            conversation_index.write_text(
                conversation_index.read_text()
                + "\n| 2026-05-19 | `design` | missing | [missing](2026-05-19_001_missing.md) |\n"
            )

            result = self.run_cli(project, "check", check=False)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("Broken link", result.stderr)

    def test_check_fails_for_missing_task_source_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.run_cli(project, "init", "--project-name", "Demo")
            self.run_cli(
                project,
                "maintain",
                "--title",
                "缺失来源链接",
                "--summary",
                "测试缺失计划来源。",
                "--implementation",
                "写入一个不存在的 from-plan。",
                "--from-plan",
                "plan-records/2026-05-19_001_missing.md",
            )

            result = self.run_cli(project, "check", check=False)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("Broken link", result.stderr)


if __name__ == "__main__":
    unittest.main()
