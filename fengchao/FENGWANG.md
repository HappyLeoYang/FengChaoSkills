# FengWang 蜂王入口

> 本文件是新 AI 会话理解 FengChaoSkills 的统一入口。先读本文件，再按 `memory-map.md` 路由到最小必要上下文。
> 最后更新：2026-07-09

## 记忆分层

| 类型 | 目录 | 语义 |
|------|------|------|
| 当前事实 | `business-context/` | 当前稳定业务真相 |
| 已落地任务 | `task-records/` | 已交付开发任务的业务意图、最终方案和证据 |
| 变更历史 | `changelog/` | 已落地代码、配置、数据库等变更历史 |
| 计划方案 | `plan-records/` | Plan 模式或方案阶段产物，不代表已落地事实 |
| 对话记忆 | `conversation-records/` | 用户解释过的业务背景、偏好、术语和边界 |

## 新需求处理流程

1. 读取本文件和 `memory-map.md`。
2. 根据用户需求中的业务词、接口、页面、数据表、状态或权限线索定位相关记录。
3. 路由结果先读前 3 条；优先读取当前事实，再读取相关对话、计划、任务和 changelog。
4. 如果记录冲突，以 `business-context` 为当前事实；`task-records/changelog` 为落地证据；`plan-records/conversation-records` 为历史参考。
5. 不全量读取所有记录，优先读取 FengWang 路由出的 8-12 个文件（输出有字节预算）。

## 维护规则

- Plan 产出后维护 `plan-records/` 和 `memory-map.md`，不写 changelog，不写业务真相。
- 有长期价值的用户业务解释维护 `conversation-records/` 和 `memory-map.md`。
- 真实开发完成后维护 `task-records/`、`changelog/`，必要时更新 `business-context/` 和 `memory-map.md`。
