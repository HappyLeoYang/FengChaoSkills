# FengWang Memory Map

> 按领域、关键词、接口、文件、状态和业务链路维护的渐进式路由表。
> 最后更新：2026-07-09

| 类型 | 状态 | 领域 | 触发词/线索 | 优先读取 | 说明 |
|------|------|------|-------------|----------|------|
| context | current | general | 项目 上下文 业务 当前事实 | [CONTEXT-INDEX.md](business-context/CONTEXT-INDEX.md) | 当前业务上下文入口 |
| task | historical | general | 任务 开发 落地 实现 | [TASK-INDEX.md](task-records/TASK-INDEX.md) | 已落地任务入口 |
| changelog | historical | general | changelog 变更 历史 代码 | [CHANGELOG-INDEX.md](changelog/CHANGELOG-INDEX.md) | 变更历史入口 |
| plan | proposed | general | plan 计划 方案 设计 | [PLAN-INDEX.md](plan-records/PLAN-INDEX.md) | 计划记录入口 |
| conversation | historical | general | 对话 解释 术语 偏好 边界 | [CONVERSATION-INDEX.md](conversation-records/CONVERSATION-INDEX.md) | 对话记忆入口 |
| plan | implemented | toolkit | 按 DESIGN v1 1 蓝图落地 M1 M4 把 FengChaoSkills 从 demo 升级为成熟开源项目 低侵入安装 可靠性内核 规模化记忆生命周期 开源发布就绪 新布局 生命周期命令 marker 块化 | [2026-07-09_001_按-design-v1.1-蓝图落地-m1-m4.md](plan-records/2026-07-09_001_按-design-v1.1-蓝图落地-m1-m4.md) | 计划阶段记录，非当前业务事实 |
| task | implemented | installer | M1 低侵入安装与生命周期 用户要求引入无痛 无感使用 停用无残留 demo 版 init 产生 5 份 skill 副本 6 个顶层目录 整文件覆写 侵入过强且无法干净卸载 在目标项目只产生 fengchao 单一工具点与单一记忆根 | [2026-07-09_001_m1-低侵入安装与生命周期.md](task-records/2026-07-09_001_m1-低侵入安装与生命周期.md) | 已落地开发任务 |
| changelog | historical | installer | M1 低侵入安装与生命周期 用户要求引入无痛 无感使用 停用无残留 demo 版 init 产生 5 份 skill 副本 6 个顶层目录 整文件覆写 侵入过强且无法干净卸载 在目标项目只产生 fengchao 单一工具点与单一记忆根 | [2026-07-09_001_m1-低侵入安装与生命周期.md](changelog/2026-07-09_001_m1-低侵入安装与生命周期.md) | 已落地变更记录 |
| task | implemented | reliability | M2 可靠性内核 hooks 硬门禁与诊断契约 prompt 约定是软的 agent 忘了维护记忆就一切归零 且 CLI 人读输出对 hook CI 是不可靠接口 真实交付的会话结束前必须存在当天 changelog 记录 由 Stop 按 | [2026-07-09_002_m2-可靠性内核：hooks-硬门禁与诊断契约.md](task-records/2026-07-09_002_m2-可靠性内核：hooks-硬门禁与诊断契约.md) | 已落地开发任务 |
| changelog | historical | reliability | M2 可靠性内核 hooks 硬门禁与诊断契约 prompt 约定是软的 agent 忘了维护记忆就一切归零 且 CLI 人读输出对 hook CI 是不可靠接口 真实交付的会话结束前必须存在当天 changelog 记录 由 Stop 按 | [2026-07-09_002_m2-可靠性内核：hooks-硬门禁与诊断契约.md](changelog/2026-07-09_002_m2-可靠性内核：hooks-硬门禁与诊断契约.md) | 已落地变更记录 |
| task | implemented | memory-model | M2 真相层 delta 语义合并与 maintain 分档 demo 版 update_domain_context 纯追加导致同一规则多版本并存 真相层退化成历史日志 且每次小修都写满一套 task record 产生记忆噪音 | [2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md](task-records/2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md) | 已落地开发任务 |
| changelog | historical | memory-model | M2 真相层 delta 语义合并与 maintain 分档 demo 版 update_domain_context 纯追加导致同一规则多版本并存 真相层退化成历史日志 且每次小修都写满一套 task record 产生记忆噪音 | [2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md](changelog/2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md) | 已落地变更记录 |
| task | implemented | routing | M3 路由打分 v2 与记忆生命周期命令 子串匹配路由在记录上几百条后会把最小上下文变成错误上下文 不可变记录只增不减需要瘦身机制 fengwang 路由采用词级匹配 中文 2 gram IDF 加权 领域命中加权 时间衰减打分 输出限制在 | [2026-07-09_004_m3-路由打分-v2-与记忆生命周期命令.md](task-records/2026-07-09_004_m3-路由打分-v2-与记忆生命周期命令.md) | 已落地开发任务 |
| changelog | historical | routing | M3 路由打分 v2 与记忆生命周期命令 子串匹配路由在记录上几百条后会把最小上下文变成错误上下文 不可变记录只增不减需要瘦身机制 fengwang 路由采用词级匹配 中文 2 gram IDF 加权 领域命中加权 时间衰减打分 输出限制在 | [2026-07-09_004_m3-路由打分-v2-与记忆生命周期命令.md](changelog/2026-07-09_004_m3-路由打分-v2-与记忆生命周期命令.md) | 已落地变更记录 |
| task | implemented | distribution | M4 开源发布就绪 双语模板 文档集与打包 项目要走向开源 需要英文模板 60 秒能看懂的 README 细分文档 PyPI 安装路径和 CI 工具通过两条对等路径分发 包 fengchao fengchao_skill 包内置完整 | [2026-07-09_005_m4-开源发布就绪：双语模板、文档集与打包.md](task-records/2026-07-09_005_m4-开源发布就绪：双语模板、文档集与打包.md) | 已落地开发任务 |
| changelog | historical | distribution | M4 开源发布就绪 双语模板 文档集与打包 项目要走向开源 需要英文模板 60 秒能看懂的 README 细分文档 PyPI 安装路径和 CI 工具通过两条对等路径分发 包 fengchao fengchao_skill 包内置完整 | [2026-07-09_005_m4-开源发布就绪：双语模板、文档集与打包.md](changelog/2026-07-09_005_m4-开源发布就绪：双语模板、文档集与打包.md) | 已落地变更记录 |
| plan | approved | distribution | 开源发布路线图 R1 R4 开源到 GitHub 让所有人可用 安装体验对齐甚至超过主流 skills 插件市场后置到种子用户测试通过之后 开源上线 建仓 占位链接替换 分支整理 CI 首跑 R2 PyPI 自动发布 包名核查 | [2026-07-09_002_开源发布路线图-r1-r4.md](plan-records/2026-07-09_002_开源发布路线图-r1-r4.md) | 计划阶段记录，非当前业务事实 |
| changelog | historical | general | R1 GitHub 开源上线 仓库正式开源至 github com HappyLeoYang FengChaoSkills squash 合入 master 并打 tag v0 2 0 配置 主远端 Gitee 双推镜像 | [2026-07-09_006_r1-github-开源上线.md](changelog/2026-07-09_006_r1-github-开源上线.md) | 已落地变更记录 |
| task | implemented | distribution | R2 PyPI 发布准备 包名定为 fengchao skills 并接入 Trusted Publishing 自动发布 核查发现 名 已被活跃包占用 ijiwei 的大模型服务 SDK v2 5 1 包名与 | [2026-07-09_006_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md](task-records/2026-07-09_006_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md) | 已落地开发任务 |
| changelog | historical | distribution | R2 PyPI 发布准备 包名定为 fengchao skills 并接入 Trusted Publishing 自动发布 核查发现 名 已被活跃包占用 ijiwei 的大模型服务 SDK v2 5 1 包名与 | [2026-07-09_007_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md](changelog/2026-07-09_007_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md) | 已落地变更记录 |
| changelog | historical | general | R2 完成 v0 2 0 经 Trusted Publishing 发布至 PyPI 并验收通过 GitHub Release 触发 release yml 首跑成功 版本校验 测试 构建 | [2026-07-09_008_r2-完成：v0.2.0-经-trusted-publishing-发布至-pypi-并验收通过.md](changelog/2026-07-09_008_r2-完成：v0.2.0-经-trusted-publishing-发布至-pypi-并验收通过.md) | 已落地变更记录 |
