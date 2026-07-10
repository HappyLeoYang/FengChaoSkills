# CI 集成

> 让"记忆维护必然发生"的最后一道防线。hook 管本地会话，CI 管合并入口。

## PR 记忆提醒（推荐起步）

把 [ci/fengchao-memory-check.yml](ci/fengchao-memory-check.yml) 复制到你项目的 `.github/workflows/`：

- PR 有代码变更但没有记忆根变更 → 自动评论提醒（附现成的 maintain 命令骨架）；
- 默认**不阻塞合并**；团队共识成熟后可把提醒步骤改为 `exit 1` 升级为必需检查；
- 同一 PR 只评论一次。

## 结构校验

在你自己的 CI 里加一步链接完整性校验（任何有 Python 3.9+ 的 runner 都能跑，零依赖）：

```yaml
- name: FengChao check
  run: python3 .fengchao/skill/scripts/fengchao.py check
```

严格模式（要求有代码变更的提交当天有 changelog，适合放在合并队列）：

```yaml
- name: FengChao strict check
  run: python3 .fengchao/skill/scripts/fengchao.py check --strict
```

## 机器可读输出

所有校验命令支持 `--format json`，方便在 CI 里做自定义处理：

```bash
python3 .fengchao/skill/scripts/fengchao.py check --format json | jq '.diagnostics[] | select(.severity=="error")'
```

诊断信封结构与退出码契约见 [DESIGN.md 附录 C](DESIGN.md)：0 通过 / 1 失败 / 2 用法错误；`--warn` 模式恒为 0（适合只提醒不阻塞的场景）。

## 本地 git 钩子（可选）

不用 GitHub Actions 的团队可以装可选的 pre-commit 提醒（默认不装，装后可干净卸载）：

```bash
python3 .fengchao/skill/scripts/fengchao.py install-git-hook        # 安装
python3 .fengchao/skill/scripts/fengchao.py install-git-hook --remove
```

行为等同 `check --warn --require-records-for-git-changes`：只提醒，不阻塞提交。

相关：[团队协作](team-workflow.md)
