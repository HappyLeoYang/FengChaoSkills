# R2 PyPI 发布准备：包名定为 fengchao-skills 并接入 Trusted Publishing 自动发布

- **记录时间**：2026-07-09 20:15
- **领域**：distribution
- **交付档位**：full
- **规则名**：发布与分发契约（change-kind：modified）
- **隐私策略**：只保存对话萃取摘要，不保存完整对话
- **关联 changelog**：`../changelog/2026-07-09_007_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md`
- **关联 plan**：
- 无
- **关联 conversation**：
- 无

## 用户真实业务诉求

R2 核查发现 PyPI 名 fengchao 已被活跃包占用（ijiwei 的大模型服务 SDK v2.5.1），包名与 console script 改定为 fengchao-skills；全部文档安装命令同步替换；新增 release.yml（GitHub Release 触发，OIDC Trusted Publishing 免 token 上传，发布前校验版本一致性并跑全量测试）；本地 wheel 构建与 fengchao-skills 命令入口实测通过

## 最终确认的业务规则

工具通过两条对等路径分发：PyPI 包 fengchao-skills（console script 同名，保证 uvx fengchao-skills 一条命令直达；fengchao_skill 包内置完整 skill 资产）与 git clone 源码直跑；运行时零第三方依赖与零遥测是不可破坏的信任承诺。

## 最终实现方案

pyproject.toml 改 name 与 [project.scripts]；README/getting-started/existing-projects/team-workflow/faq/troubleshooting/DESIGN/release-plan 同步命令名；.github/workflows/release.yml 新增；ci.yml actions 升级消除 Node 20 弃用警告；决策登记于 release-plan.md 已定决策第 10 条

## 关键决策与取舍

本次未记录额外取舍。

## 涉及范围

| 类型 | 内容 |
|------|------|
| 领域 | `distribution` |
| 文件 | 未记录 |

## 实现证据

- 未记录

## 验证结果

- 未记录

## 后续风险或待确认点

暂无。
