# 故障排查

## check 报 broken_link

```
[error] broken_link: Broken link in fengchao/task-records/TASK-INDEX.md: ...
```

某条索引/记录里的链接指向不存在的文件。常见原因：记录被手工改名或删除、归档后有残留旧链接。处理：

1. `fengchao doctor` — 如果目标文件其实被移动/归档了，会给出 `index_dead_row` 和新位置；
2. 按 fix 建议修正链接后重跑 `check`。

## maintain 报 rule_already_exists / rule_not_found

这是 B4 语义合并的保护，不是 bug：

- `rule_already_exists`：你用 `--change-kind added` 写了一个已存在的规则名 → 改用 `modified`，或确认是新规则后换名；
- `rule_not_found`：`modified/removed` 找不到规则名 → 看错误信息里的现有规则清单和最相近候选，规则名是稳定 key，不要因为内容变了就换名。

失败时**没有任何文件被写入**，直接修正参数重跑即可。

## Stop hook 一直提醒 / 从不提醒

- 一直提醒：确认当天交付后是否真的跑了 `maintain`（lite 档也会写 changelog，写了就不再提醒）；同一会话只提醒一次，如果每个新会话都提醒，说明确实有未记账的变更。
- 从不提醒：检查 `.fengchao/config.yaml` 的 `hook_mode` 是否为 `off`、`enabled` 是否为 `true`；确认 `.claude/settings.json` 里有 `fengchao.py hook` 条目（`disable` 会摘除它们）。
- 想彻底关掉：`hook_mode: "off"`，或 `init --no-hooks`。

## status 显示 legacy_layout

项目还是 v0.1 的老布局（六个记忆目录散在根下）：

```bash
python3 skills/fengchao-business-memory/scripts/fengchao.py migrate   # 迁移到单一记忆根
python3 .fengchao/skill/scripts/fengchao.py upgrade                   # 刷新宿主注入路径
```

迁移自动改写所有相对链接并跑 check；绝不修改记忆内容本身。

## status 显示 version_drift

项目内安装的工具版本落后于当前 CLI。`fengchao upgrade` 重写 `.fengchao/skill/`、薄入口、薄命令和 marker 块——**不碰记忆根**。

## disable 之后 opencode.json 还在

`disable` 只删除内容与 FengChao 生成物完全一致的 `opencode.json`；如果你在里面加过自己的配置，它会被保留（我们不动用户文件），手工移除 instructions 里的 FengChao 条目即可。

## memory-map 有重复行 / 超长行警告

```bash
python3 .fengchao/skill/scripts/fengchao.py compact   # 去重、重排、折叠归档行
```

`memory_map_row_too_long` 警告说明某行触发词超过 120 字符上限，compact 或手工精简即可。

## 找不到相关记忆（路由空结果）

- 查询词太泛或太偏：换业务词（界面名、状态名、角色名）重试；
- 记录确实不存在：读 `fengchao/FENGWANG.md` + `business-context/CONTEXT-INDEX.md` 建立全局图；
- 输出被截断：`(已截断：还有 N 条低分匹配)` 说明预算用尽，细化查询词而不是调大 `--budget`。

其他问题请提 issue（附 `fengchao status --format json` 输出）。
