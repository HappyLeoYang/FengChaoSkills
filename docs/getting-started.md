# 快速上手

> 目标：5 分钟内完成安装并跑通第一次 maintain。核心概念见 [concepts.md](concepts.md)。

## 1. 安装

```bash
cd your-project

# 推荐：免安装一次性运行
uvx fengchao-skills init
# 没有 uv？一次性安装：brew install uv（或直接用下面的源码方式，零前置依赖）

# 或从源码（零依赖，任何有 Python 3.9+ 的机器都能跑）
git clone https://github.com/HappyLeoYang/FengChaoSkills.git ~/FengChaoSkills
python3 ~/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py init
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--agents claude,cursor` | 指定接入的 agent；缺省时自动探测 `.claude/`、`.cursor/` 等目录 |
| `--memory-only` | 只要记忆结构，不装 skill、不写任何宿主注入 |
| `--no-hooks` | 不注册 Claude Code hooks |
| `--hook-mode strict` | Stop 门禁升级为阻塞模式（默认 remind） |
| `--language en` | 生成英文模板 |
| `--memory-root <dir>` | 自定义记忆根目录名（默认 `fengchao`） |

安装后验证：

```bash
python3 .fengchao/skill/scripts/fengchao.py status
```

## 2. 第一次真实交付后

完成一次真实开发交付后（AI 会被 skill 规则和 Stop hook 提醒，也可以手动执行）：

```bash
# 有业务含义的交付（full 档）
python3 .fengchao/skill/scripts/fengchao.py maintain \
  --title "设计单两级审核" \
  --summary "审核漏批风险，要求增加经理终审" \
  --implementation "审核状态机新增 manager-review 阶段" \
  --business-change "设计单最终通过必须依次经过主管审核和经理审核。" \
  --change-kind added --rule-name "设计单审核流程" \
  --scenario "主管一审通过、经理二审通过才进入已通过状态" \
  --domain design

# 纯修复/重构（lite 档）：不给 --business-change 即可，只记一条 changelog
python3 .fengchao/skill/scripts/fengchao.py maintain \
  --title "修复审核列表空指针" --summary "无历史记录时报错" --implementation "补空值判断"
```

档位判定一句话：**半年后的新会话是否需要知道这次改动的"为什么"？** 需要 → full；不需要 → lite。

## 3. 新会话找回记忆

```bash
python3 .fengchao/skill/scripts/fengchao.py fengwang --query "设计单审核"
```

或在 Claude Code 中直接 `/fengchao:route 设计单审核`。装了 hooks 的项目连这一步都不需要——SessionStart hook 会自动提示 AI 先读路由入口。

## 4. 校验与体检

```bash
python3 .fengchao/skill/scripts/fengchao.py check           # 链接完整性 + 必需文件
python3 .fengchao/skill/scripts/fengchao.py check --strict  # 额外要求 git 变更当天有 changelog
python3 .fengchao/skill/scripts/fengchao.py doctor          # 深度体检：孤儿记录、死行、老式条目
```

## 5. 停用 / 卸载

```bash
python3 .fengchao/skill/scripts/fengchao.py disable    # 暂停（enable 逐字节还原）
python3 .fengchao/skill/scripts/fengchao.py uninstall  # 移除工具，记忆保留
```

下一步：[团队协作最佳实践](team-workflow.md) · [在已有大项目中引入](existing-projects.md)
