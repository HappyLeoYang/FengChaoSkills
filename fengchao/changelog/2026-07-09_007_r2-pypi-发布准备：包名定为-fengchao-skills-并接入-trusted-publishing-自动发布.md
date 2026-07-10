# R2 PyPI 发布准备：包名定为 fengchao-skills 并接入 Trusted Publishing 自动发布

- **变更时间**：2026-07-09 20:15
- **领域**：distribution
- **变更类型**：development
- **关联任务记录**：`../task-records/2026-07-09_006_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md`

## 变更概述

R2 核查发现 PyPI 名 fengchao 已被活跃包占用（ijiwei 的大模型服务 SDK v2.5.1），包名与 console script 改定为 fengchao-skills；全部文档安装命令同步替换；新增 release.yml（GitHub Release 触发，OIDC Trusted Publishing 免 token 上传，发布前校验版本一致性并跑全量测试）；本地 wheel 构建与 fengchao-skills 命令入口实测通过

## 业务变化

工具通过两条对等路径分发：PyPI 包 fengchao-skills（console script 同名，保证 uvx fengchao-skills 一条命令直达；fengchao_skill 包内置完整 skill 资产）与 git clone 源码直跑；运行时零第三方依赖与零遥测是不可破坏的信任承诺。

## 实现说明

pyproject.toml 改 name 与 [project.scripts]；README/getting-started/existing-projects/team-workflow/faq/troubleshooting/DESIGN/release-plan 同步命令名；.github/workflows/release.yml 新增；ci.yml actions 升级消除 Node 20 弃用警告；决策登记于 release-plan.md 已定决策第 10 条

## 涉及文件

- 未记录

## 验证

- 未记录
