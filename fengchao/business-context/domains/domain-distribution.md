# distribution 领域上下文

> 最后更新：2026-07-09

## 领域定位

待补充：描述该领域在 FengChaoSkills 中负责的业务问题。

## 当前业务规则

### 规则：发布与分发契约
- **规则**：工具通过两条对等路径分发：PyPI 包 fengchao-skills（console script 同名，保证 uvx fengchao-skills 一条命令直达；fengchao_skill 包内置完整 skill 资产）与 git clone 源码直跑；运行时零第三方依赖与零遥测是不可破坏的信任承诺。
- **场景**：干净机器 pip install fengchao-skills 后执行 fengchao-skills init（或免安装 uvx fengchao-skills init），能装出与源码路径完全一致的 .fengchao/skill/ 副本并通过 check；误敲 uvx fengchao 不会装到本项目，文档中绝不出现裸 fengchao 安装命令。
- **来源**：[2026-07-09_006_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md](../../task-records/2026-07-09_006_r2-pypi-发布准备：包名定为-fengchao-skills-并接入-trusted-publishing-自动发布.md)
- **生效**：2026-07-09
- **沿革**：[2026-07-09_005_m4-开源发布就绪：双语模板、文档集与打包.md](../../task-records/2026-07-09_005_m4-开源发布就绪：双语模板、文档集与打包.md)

## 已废除规则

（暂无）

## 核心入口

| 类型 | 路径/接口 | 说明 |
|------|-----------|------|
| 待补充 | 待补充 | 待补充 |

## 上下游关系

待补充：记录该领域依赖谁、影响谁。
