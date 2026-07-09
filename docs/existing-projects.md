# 在已有大项目中引入

> FengChao 是事后记账系统，不要求项目从第一天就使用。本文讲如何在一个已运行多年的项目中安全引入。

## 引入是低侵入的

对已有项目执行 `init`：

- 已有的 `CLAUDE.md` / `AGENTS.md` **原内容一字不动**，只追加一个 ≤15 行的 marker 块；
- 已有的 `opencode.json` 不会被覆盖（打印手工合并指引）；
- 新增顶层可见目录只有一个记忆根 `fengchao/`（外加隐藏的 `.fengchao/`）；
- 随时 `disable` 精确摘除全部注入，`git diff` 干净可读。

```bash
cd legacy-project
uvx fengchao init --agents claude    # 只接入你在用的工具
```

## 不要试图一次性补全历史

**不要**让 AI 读全部代码然后批量生成"业务上下文"——那会把猜测写进真相层（违反触发边界）。正确的做法是让记忆自然生长：

1. init 后 `business-context/` 只有空脚手架，这是正常状态；
2. 每次真实交付用 `maintain` 记一条，规则条目逐个沉淀；
3. 用户解释业务时用 `/fengchao:remember` 捕获术语和边界；
4. 两三周后，高频改动的领域自然会有最有价值的记忆。

## 可以手工播种的两类内容

例外是两类**你确定为当前事实**的内容，可以在引入时人工整理：

- `business-context/debt-registry.md`：已知的坑、技术债、"改这里必须同时看那里"；
- `conversation-records/`：团队约定俗成的术语表（用 `conversation --term` 逐条录入，标记 `--promote confirmed`）。

规则条目不建议手工播种——没有 task-record 证据链的"规则"正是 FengChao 要消灭的"我记得是这样"。

## 大仓库注意事项

- `check --strict` 依赖 `git status`，在超大仓库上首次运行可能慢，hook 用的正是它——如果项目 `git status` 本身 >500ms，建议 `hook_mode: "off"` 并改用 CI 检查；
- 路由预算默认 4KB，记录上几百条后建议定期 `archive --before` + `compact`；
- 多模块 monorepo：在每个业务模块根目录独立 init（各自一个记忆根），比全仓库共用一个记忆根路由更准。

相关：[团队协作](team-workflow.md) · [故障排查](troubleshooting.md)
