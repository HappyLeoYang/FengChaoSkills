# FAQ

## 会不会拖慢我的 AI 会话？

不会。路由输出是最小集合且有 4KB 字节预算（超限截断并提示细化查询词）；hook 是本地 Python 脚本，执行 < 500ms；全程零网络请求。

## 会多消耗多少 tokens？（实测数据）

很少，而且是可量化的（以下为 v0.2.1 实测，token 按 CJK 1 字/token、英文 3 字符/token 的保守上界折算）：

| 注入项 | 时机 | 实测大小 | tokens 上界 |
|--------|------|----------|-------------|
| CLAUDE.md marker 块 | 每会话常驻 | 480 B | ≤ 154 |
| SessionStart hook 注入 | 每会话一次 | 325 B | ≤ 105 |
| `fengwang --query` 路由输出 | 按需查询 | 实测 1.1 KB（硬预算 4 KB） | 实测 ≤ 351（打满预算也 ≤ 约 1400） |
| Stop hook 提醒（含 maintain 骨架） | 仅真实交付会话一次 | 501 B | ≤ 165 |

即：**每会话固定开销 ≤ 约 260 tokens**（相当于一句多点的话）；新会话完整路由一次（读 FENGWANG.md 入口 + 一次查询 + 按需读前 3 条记录）约 1–2K tokens。对照组不是零——不用它时，每个新会话重新解释业务通常要几百到几千 tokens 的往返，还有 AI 猜错业务返工的开销。**只要路由让你少解释一句业务，本轮就回本了。**

## 记忆会不会泄露对话隐私？

默认 summary-only：只保存萃取后的业务摘要，永不保存完整对话。记忆是仓库里的 Markdown，你可以像 review 代码一样 review 每一条记忆（见[团队协作](team-workflow.md)）。工具本身零遥测、零网络请求。

## 和 OpenSpec / GitHub Spec Kit 冲突吗？

不冲突。它们的 truth 是需求规范（事前：AI 接下来该做什么），FengChao 的 truth 是业务认知（事后：为什么、术语、边界、坑、否定项）。OpenSpec 管变更生命周期，FengChao 管业务认知生命周期，可以在同一个项目里共存。

## 不用 Claude Code 能用吗？

能。五个 agent surface（Claude Code / Cursor / OpenCode / Codex / 通用 AGENTS.md）都有薄入口；hooks 硬门禁目前只有 Claude Code 支持，其他工具可用 `fengchao-skills install-git-hook` 装可选的 git pre-commit 提醒兜底。效果分级：Claude Code（全自动）> Cursor/OpenCode（规则驱动 + 手动命令）> 纯 AGENTS.md（约定驱动）。

## AI 忘了维护记忆怎么办？

这是同类工具最常见的失败模式，FengChao 用三层保险应对：① skill 规则要求交付后维护；② Stop hook 检测"有 git 变更但当天无 changelog"并提醒（remind）或阻塞（strict）；③ CI 检查 PR 是否附带记忆变更（见 [ci.md](ci.md)）。

## 每次小修小补都要写一堆记录吗？

不用。纯修复/重构/杂务走 lite 档：不提供 `--business-change`，只记一条 changelog。判定标准一句话：半年后的新会话是否需要知道这次改动的"为什么"？

## 记录多了会不会越来越难用？

路由打分是词级匹配 + IDF 加权 + 时间衰减，几百条记录下仍然精准；`archive --before` 把老记录移入归档（链接不断），`compact` 重建 memory-map，`doctor` 检出孤儿记录和死行。

## 想换个工具/不想用了怎么办？

`fengchao-skills uninstall` 移除工具本体，记忆是一套完好的人类可读 Markdown 文档库，永远属于你。这是设计红线：升级、迁移、卸载都不碰记忆数据。

## 从旧版（六目录散在根下）怎么升级？

`fengchao-skills migrate` 一键迁移到单一记忆根布局，自动改写指向记忆目录的相对链接（指向记忆根外项目文件的链接原样保留）并跑 check 验证；然后 `fengchao-skills upgrade` 刷新宿主注入。见[故障排查](troubleshooting.md)。
