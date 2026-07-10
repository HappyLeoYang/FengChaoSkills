# FengChaoSkills 渐进式上下文入口

> 本文件是 AI 理解项目业务上下文的第一入口。普通讨论、Plan 模式、只读分析不会更新本体系；只有实际开发交付后才维护。
> 最后更新：2026-07-09

## 项目定位

待补充：用一句话描述本项目服务的业务、用户和核心流程。

## 阅读路径

1. 新会话先读取 `../FENGWANG.md` 和 `../memory-map.md`，按需求路由到最小必要上下文。
2. 再读本文件，建立项目全局业务地图。
3. 按需求所属领域读取 `domains/domain-*.md`。
4. 涉及跨模块影响时读取 `impact-matrix.md`。
5. 需要追溯历史时读取 `../task-records/TASK-INDEX.md`、`../plan-records/PLAN-INDEX.md`、`../conversation-records/CONVERSATION-INDEX.md` 和 `../changelog/CHANGELOG-INDEX.md`。

## 领域索引

| 领域 | 文档 | 状态 |
|------|------|------|
| 待识别 | `domains/domain-general.md` | 初始化 |

## 关键业务链路

待补充：用 Mermaid 或短列表描述项目主业务链路。

## 变更维护规则

- 实际开发完成后必须生成不可变任务记录和 changelog。
- 只有稳定、已落地的业务事实才能合并进 `business-context/`。
- 每条当前业务认知都应能追溯到任务记录或 changelog。
