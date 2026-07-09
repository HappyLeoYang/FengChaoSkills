# 核心概念

> FengChao 的四个核心设计原则与六层记忆模型。术语速查见 [glossary.md](glossary.md)。

## 四个核心设计原则

1. **记忆有可信度等级**。六个目录不是文件分类，是认识论分层：当前真相 / 落地证据 / 历史参考。冲突时优先级：`business-context` > `task-records/changelog` > implemented plan > `conversation-records` > proposed plan。
2. **写入有触发边界**。只有真实开发交付才能写证据层；讨论、Plan、只读分析不许污染记忆。
3. **真相有证据链**。每条业务认知必须能追溯到任务记录；`check` 强制校验链接完整性。
4. **读取有路由**。FengWang 保证新会话加载最小必要上下文（8–12 个文件，4KB 输出预算），而不是全量历史。

## 六层记忆模型

| 目录 | 语义 | 可变性 |
|------|------|--------|
| `business-context/` | 当前业务真相 | 可变（始终代表最新） |
| `task-records/` | 已交付任务的业务意图、最终方案、证据 | 不可变 |
| `changelog/` | 已落地变更历史 | 不可变 |
| `plan-records/` | 最终计划（proposed/approved/implemented/…） | 状态可更新（`plan-status` 命令） |
| `conversation-records/` | 用户业务解释、术语、偏好、否定项 | 不可变 |
| `FENGWANG.md` + `memory-map.md` | 路由入口 | 持续追加，`compact` 可重建 |

## 规则条目与 delta 语义合并

`business-context/` 的 domain 文件中，每条业务规则是一个结构化条目，以**规则名为稳定 key**：

```markdown
### 规则：设计单审核流程
- **规则**：设计单最终通过必须依次经过主管审核和经理审核。
- **场景**：设计师提交后，主管一审通过、经理二审通过才进入"已通过"状态。
- **来源**：[task-record 链接]
- **生效**：2026-07-09
- **沿革**：[历任旧版本 task-record 链接]
```

写入只能通过 `maintain --business-change --change-kind added|modified|removed --rule-name ...`：

- **added**：规则名已存在则整体失败（防重复条目）；
- **modified**：整块替换正文，旧来源链接自动进"沿革"（保链不保文——旧文本在不可变的旧 task-record 里）;
- **removed**：条目移入"已废除规则"段。

这保证**同一规则在同一时刻只有一个现行条目**——真相层永远不会退化成历史日志。

## lite / full 分档

不是每次交付都值得完整仪式。判定标准一句话：**半年后的新会话是否需要知道这次改动的"为什么"？**

| 档位 | 触发 | 写入 |
|------|------|------|
| full | 提供 `--business-change` | task-record + changelog + 语义合并 + memory-map |
| lite | 未提供 | 仅 changelog + memory-map 一行 |

逃生舱：`--with-task-record` 让 lite 交付也留 task-record（如重大重构）。

## 硬门禁（hooks）

prompt 约定是软的，hook 是硬的。`init` 默认向 `.claude/settings.json` 注册：

- **SessionStart**：自动注入"先读 FENGWANG.md 路由"的上下文，路由无需用户提醒；
- **Stop**：检测"有项目 git 变更但当天无 changelog"，按 `hook_mode` 行动——`remind`（非阻塞提示 + maintain 命令骨架）/ `strict`（block，要求先维护记忆）/ `off`。

防打扰设计：同一会话最多提醒一次；纯记忆目录变更不触发；无 git 仓库静默跳过。

## 诊断契约

所有校验类命令支持 `--format json`，输出统一诊断信封 `{severity, code, message, target?, fix?}`，每条诊断自带可执行的修复建议。退出码：0 成功 / 1 校验或合并失败 / 2 用法错误 / 130 用户取消。完整 code 登记表见 [DESIGN.md 附录 C](DESIGN.md)。
