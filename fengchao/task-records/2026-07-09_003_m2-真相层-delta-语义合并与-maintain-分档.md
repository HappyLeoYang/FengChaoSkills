# M2 真相层 delta 语义合并与 maintain 分档

- **记录时间**：2026-07-09 02:18
- **领域**：memory-model
- **交付档位**：full
- **规则名**：真相层唯一现行原则（change-kind：added）
- **隐私策略**：只保存对话萃取摘要，不保存完整对话
- **关联 changelog**：`../changelog/2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md`
- **关联 plan**：
- [plan-records/2026-07-09_001_按-design-v1.1-蓝图落地-m1-m4.md](../plan-records/2026-07-09_001_按-design-v1.1-蓝图落地-m1-m4.md)
- **关联 conversation**：
- 无

## 用户真实业务诉求

demo 版 update_domain_context 纯追加导致同一规则多版本并存，真相层退化成历史日志；且每次小修都写满一套 task-record 产生记忆噪音。

## 最终确认的业务规则

business-context 中同一规则名在同一时刻只能有一个现行条目：maintain 必须以 added/modified/removed 语义写入（modified 整块替换、旧来源进沿革，removed 移入已废除段），合并失败则整体失败不落盘；无业务含义的交付走 lite 档只记 changelog。

## 最终实现方案

merge_domain_rule() 先验证后写入；规则条目按附录 B 格式（规则/场景/来源/生效/沿革）；rule_already_exists/rule_not_found 诊断附最相近候选；B5 lite/full 判定与 --with-task-record 逃生舱；check --strict 对 lite 交付放宽为查 changelog。

## 关键决策与取舍

本次未记录额外取舍。

## 涉及范围

| 类型 | 内容 |
|------|------|
| 领域 | `memory-model` |
| 文件 | `skills/fengchao-business-memory/scripts/fengchao.py` |

## 实现证据

- tests DeltaMergeTests/MaintainTierTests

## 验证结果

- added→modified→modified 单条目断言、removed 废除段断言、错误组合无半成品断言全部通过

## 后续风险或待确认点

暂无。
