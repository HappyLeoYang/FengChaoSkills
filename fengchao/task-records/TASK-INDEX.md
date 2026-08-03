# 任务记录索引

> 不可变任务记录的渐进式入口。记录实际开发交付后的业务意图、最终方案和实现证据。
> 最后更新：2026-07-09

## 最近任务

| 日期 | 领域 | 任务 | 业务变化 | 记录 |
|------|------|------|----------|------|
| 2026-07-09 | `installer` | M1 低侵入安装与生命周期 | init 在目标项目只产生 .fengchao/ 单一工具点与单一记忆根（默认 fengchao/）；宿主文件注入一律 marker 块化；disable/enable 逐字节可逆，uninstall 永不触碰记忆数据。 | [2026-07-09_001_m1-低侵入安装与生命周期.md](2026-07-09_001_m1-低侵入安装与生命周期.md) |
| 2026-07-09 | `reliability` | M2 可靠性内核：hooks 硬门禁与诊断契约 | 真实交付的会话结束前必须存在当天 changelog 记录，由 Stop hook 按 hook_mode（remind/strict/off）执行门禁；校验类命令输出统一诊断信封（severity/code/message/target/fix）并遵守 0/1/2/130 退出码契约。 | [2026-07-09_002_m2-可靠性内核：hooks-硬门禁与诊断契约.md](2026-07-09_002_m2-可靠性内核：hooks-硬门禁与诊断契约.md) |
| 2026-07-09 | `memory-model` | M2 真相层 delta 语义合并与 maintain 分档 | business-context 中同一规则名在同一时刻只能有一个现行条目：maintain 必须以 added/modified/removed 语义写入（modified 整块替换、旧来源进沿革，removed 移入已废除段），合并失败则整体失败不落盘；无业务含义的交付走 lite 档只记 changelog。 | [2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md](2026-07-09_003_m2-真相层-delta-语义合并与-maintain-分档.md) |
| 2026-07-09 | `routing` | M3 路由打分 v2 与记忆生命周期命令 | fengwang 路由采用词级匹配（中文 2-gram）+ IDF 加权 + 领域命中加权 + 时间衰减打分，输出限制在 4KB 字节预算内、超限截断并提示细化查询词，约定先读前 3 条。 | [2026-07-09_004_m3-路由打分-v2-与记忆生命周期命令.md](2026-07-09_004_m3-路由打分-v2-与记忆生命周期命令.md) |
| 2026-07-09 | `distribution` | M4 开源发布就绪：双语模板、文档集与打包 | 工具通过两条对等路径分发：PyPI 包 fengchao（fengchao_skill 包内置完整 skill 资产，支持 uvx/pipx 免安装运行）与 git clone 源码直跑；运行时零第三方依赖与零遥测是不可破坏的信任承诺。 | [2026-07-09_005_m4-开源发布就绪：双语模板、文档集与打包.md](2026-07-09_005_m4-开源发布就绪：双语模板、文档集与打包.md) |
| 2026-07-09 | `distribution` | R2 PyPI 发布准备：包名定为 fengchao-skills 并接入 Trusted Publishing 自动发布 | 工具通过两条对等路径分发：PyPI 包 fengchao-skills（console script 同名，保证 uvx fengchao-skills 一条命令直达；fengchao_skill 包内置完整 skill 资产）与 git clone 源码直跑；运行时零第三方依赖与零遥测是不可破坏的信任承诺。 | [2026-07-09_006_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md](2026-07-09_006_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md) |
| 2026-08-02 | `reliability` | v0.2.1：hook 任意 cwd 生效（F-005） | 记忆维护硬门禁在任意工作目录下生效：Stop/SessionStart hook 命令经 $CLAUDE_PROJECT_DIR 锚定项目根（缺失时回退旧相对路径行为），hook 子命令自身按 env→向上查找→cwd 解析项目根；真实交付的会话结束前必须存在当天 changelog 记录，按 hook_mode 三档执行；HOOK_COMMAND_PREFIX 每次变更必须把旧值追加进 LEGACY 清单且永不删除，保证任何历史版本写入的 hook 都能被对称摘除。 | [2026-08-02_001_v0.2.1：hook-任意-cwd-生效（f-005）.md](2026-08-02_001_v0.2.1：hook-任意-cwd-生效（f-005）.md) |
| 2026-08-02 | `memory-model` | v0.2.1：migrate 链接改写边界修复（F-003）+ 安装文档与 token 实测 | migrate 迁移老布局时只改写指向记忆内部目录（business-context/task-records/changelog/plan-records/conversation-records）的相对链接；指向记忆根之外项目文件（docs/、ui/ 等）的链接必须原样保留——新旧位置同深度，外部 ../ 本就正确。 | [2026-08-02_002_v0.2.1：migrate-链接改写边界修复（f-003）+-安装文档与-token-实测.md](2026-08-02_002_v0.2.1：migrate-链接改写边界修复（f-003）+-安装文档与-token-实测.md) |
