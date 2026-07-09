# 团队协作最佳实践

> 业务记忆是团队资产。本文讲如何在多人协作中共享和 review 记忆。

## 记忆根入 git

记忆根（默认 `fengchao/`）应该提交进仓库：

- 业务记忆随代码一起 clone、一起分支、一起合并；
- PR 里 review 记忆变更就像 review 代码——一条错误的"业务真相"比一个 bug 更危险；
- `git blame` 天然回答"这条业务认知是谁在什么时候确立的"。

`.fengchao/` 工具目录也建议入 git（团队成员 clone 后即用，无需各自 init）；`.fengchao/tmp/`（hook 防重标记）已被自动生成的 `.fengchao/.gitignore` 排除。

## PR 约定

建议团队约定：**带业务规则变化的 PR 应包含对应 task-record**。

- 用 [docs/ci/fengchao-memory-check.yml](ci/fengchao-memory-check.yml) 自动提醒：PR 有代码变更但无记忆变更时自动评论（默认不阻塞合并，团队可自行升级为必需检查）。
- review 记忆变更时重点看三处：规则条目的"规则"句是否是业务事实（而非实现细节）、"场景"是否可判定、"来源"链接是否指向真实 task-record。

## 新成员 onboarding

新成员接手业务上下文只需读两个文件：

1. `fengchao/FENGWANG.md` — 记忆分层和路由方式；
2. `fengchao/business-context/CONTEXT-INDEX.md` — 项目全局业务地图。

这本身就是引入 FengChao 的核心收益之一：业务知识不再只存在于老成员脑子里。

## 冲突处理

- 记录文件按 `日期_序号_标题` 命名，多人同日交付极少冲突；冲突时保留双方（序号顺延）。
- `memory-map.md` 是追加式表格，git 合并冲突直接两边都保留，然后跑 `fengchao compact` 去重重排。
- domain 文件的规则条目冲突说明两人改了同一条业务规则——这是**真正的业务冲突**，应该当面对齐后用一次 `maintain --change-kind modified` 收敛。

## 多 agent 团队

团队成员用不同 AI 工具（Claude Code / Cursor / Codex）没关系：记忆是共享的 Markdown，五个 surface 的薄入口都指向同一份 `.fengchao/skill/`。各成员可以只 `init --agents` 自己用的工具，宿主注入互不干扰。

相关：[在已有大项目中引入](existing-projects.md) · [CI 集成](ci.md)
