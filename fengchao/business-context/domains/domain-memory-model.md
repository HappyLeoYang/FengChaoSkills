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

### 规则：migrate 链接改写边界
- **规则**：migrate 迁移老布局时只改写指向记忆内部目录（business-context/task-records/changelog/plan-records/conversation-records）的相对链接；指向记忆根之外项目文件（docs/、ui/ 等）的链接必须原样保留——新旧位置同深度，外部 ../ 本就正确。
- **场景**：老布局项目的 memory-map 同时含指向 `../task-records/x.md` 的任务链接与指向 `../docs/y.md` 的外部文档链接：migrate 后前者剥为 `task-records/x.md`、后者保持 `../docs/y.md`，收尾 check 零 broken_link；曾有真实项目 7 个外部链接被误剥需人工还原，修复后全自动。
- **来源**：[2026-08-02_002_v0.2.1：migrate-链接改写边界修复（f-003）+-安装文档与-token-实测.md](../../task-records/2026-08-02_002_v0.2.1：migrate-链接改写边界修复（f-003）+-安装文档与-token-实测.md)
- **生效**：2026-08-02

### 规则：maintain 来源链接归一契约
- **规则**：maintain 的 --from-plan/--from-conversation 接受裸记录名、记忆根相对路径、项目根相对路径三种写法，CLI 统一归一为记忆根相对完整路径：剥记忆根前缀后，值内不含 / 时补默认目录段（plan-records/ 或 conversation-records/），无 .md 时补后缀；以 ../ 开头的视为调用方显式指定的记忆根外引用，原样保留不做任何补全。
- **场景**：传裸名 2026-08-10_001_测试对话 时 task-record 生成 ](../conversation-records/2026-08-10_001_测试对话.md) 且 check 零 broken_link；传 conversation-records/x.md 与 fengchao/conversation-records/x.md 结果一致；传 ../docs/业务文档.md 保持原样。
- **来源**：[2026-08-10_001_v0.2.2：maintain-来源链接补全（f-006）.md](../../task-records/2026-08-10_001_v0.2.2：maintain-来源链接补全（f-006）.md)
- **生效**：2026-08-10

## 已废除规则

（暂无）

## 核心入口

| 类型 | 路径/接口 | 说明 |
|------|-----------|------|
| 待补充 | 待补充 | 待补充 |

## 上下游关系

待补充：记录该领域依赖谁、影响谁。
