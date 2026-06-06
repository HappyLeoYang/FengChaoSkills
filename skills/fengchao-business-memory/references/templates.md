# Manual Templates

Use these only when the CLI is insufficient.

## Task Record

```markdown
# <Title>

- **记录时间**：YYYY-MM-DD HH:mm
- **领域**：<domain>
- **隐私策略**：只保存对话萃取摘要，不保存完整对话
- **关联 changelog**：`../changelog/<file>.md`

## 用户真实业务诉求

<summary>

## 最终确认的业务规则

<stable landed business rule, or "本次没有稳定业务规则变化。">

## 最终实现方案

<what was actually delivered>

## 关键决策与取舍

<decisions>

## 涉及范围

<domains, APIs, files, data, permissions, states>

## 实现证据

<files, diff summary, tests, logs>

## 验证结果

<verification>

## 后续风险或待确认点

<risks>
```

## Changelog Entry

```markdown
# <Title>

- **变更时间**：YYYY-MM-DD HH:mm
- **领域**：<domain>
- **变更类型**：<development/fix/refactor/config/docs>
- **关联任务记录**：`../task-records/<file>.md`

## 变更概述

<summary>

## 业务变化

<business change or "本次没有稳定业务规则变化。">

## 实现说明

<implementation notes>

## 涉及文件

<files>

## 验证

<verification>
```
