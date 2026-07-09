# 术语表

| 术语 | 含义 |
|------|------|
| 蜂巢（FengChao） | 本项目：项目业务记忆的整体系统 |
| 蜂王（FengWang） | 记忆路由入口：FENGWANG.md + memory-map.md + `fengwang --query` |
| 业务真相（business truth） | 已落地、经证据支撑的当前业务事实，存于 business-context |
| 证据层 | task-records + changelog：不可变的交付证据 |
| 参考层 | plan-records + conversation-records：历史/上下文记忆，默认不是真相 |
| 提升（promotion） | 参考层信息经确认/落地后进入 business-context 的过程 |
| 否定记忆 | 用户明确拒绝过的方案的记录，防止 AI 重复提议 |
| 记忆根（memory root） | 存放全部记忆的唯一目录（默认 `fengchao/`），属于用户、建议入 git |
| 薄入口 | 放在各 agent 目录下、仅指向 `.fengchao/skill/` 的最小文件 |
| 薄命令 | init 按 agent 生成的斜杠命令文件（route/remember/status 三动词），逻辑在 CLI 引擎 |
| marker 块 | `<!-- FENGCHAO-BUSINESS-MEMORY:START/END -->` 包裹的注入内容，保证可干净摘除 |
| 硬门禁 | 通过 hooks / check 强制记忆维护发生的机制，区别于 prompt 软约定 |
| 规则条目 | business-context 中一条结构化的现行业务规则，以规则名为稳定 key |
| 稳定 key | 规则条目的规则名：一经确立不随内容变化，是 delta 合并的定位锚点 |
| delta 合并 | maintain 以 added/modified/removed 语义写入真相层，替换/移除而非堆积 |
| 沿革 | 规则条目历任旧版本的 task-record 链接链（保链不保文） |
| 轻档/重档（lite/full） | maintain 的两档仪式：无业务变化只记 changelog；有业务变化走完整链路 |
| 诊断信封 | CLI 机器可读输出的统一结构 `{severity, code, message, target?, fix?}` |
| 老布局（legacy layout） | v0.1 的布局：六个记忆目录散在项目根下；`migrate` 一键迁移 |
| dogfooding | 本仓库用 FengChao 记录自身开发，既是测试也是活示例（见 `fengchao/`） |

更多背景见 [concepts.md](concepts.md) 与 [DESIGN.md](DESIGN.md) 附录 A。
