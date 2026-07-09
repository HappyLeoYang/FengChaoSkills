# memory-model 领域上下文

> 最后更新：2026-07-09

## 领域定位

待补充：描述该领域在 FengChaoSkills 中负责的业务问题。

## 当前业务规则

### 规则：真相层唯一现行原则
- **规则**：business-context 中同一规则名在同一时刻只能有一个现行条目：maintain 必须以 added/modified/removed 语义写入（modified 整块替换、旧来源进沿革，removed 移入已废除段），合并失败则整体失败不落盘；无业务含义的交付走 lite 档只记 changelog。
- **场景**：对同一 --rule-name 依次执行 added→modified→modified，domain 文件始终只有一个现行条目且沿革链接完整；纯 bugfix 不带 --business-change 时只产生一条 changelog。
- **来源**：[2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md](../../task-records/2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md)
- **生效**：2026-07-09

## 已废除规则

（暂无）

## 核心入口

| 类型 | 路径/接口 | 说明 |
|------|-----------|------|
| 待补充 | 待补充 | 待补充 |

## 上下游关系

待补充：记录该领域依赖谁、影响谁。
