# 演示样例

> 一个可以直接复制执行的完整生命周期演示：init → 开发 → 自动维护 → 路由 → 停用。
> 本仓库自身的 `fengchao/` 目录是真实的 dogfooding 记录，也是最好的活示例。

## 完整演示脚本

在任意空目录执行（假设已 clone 本仓库到 `~/FengChaoSkills`）：

```bash
CLI=~/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py
mkdir demo-project && cd demo-project && git init

# ① 初始化（60 秒）
python3 $CLI init --project-name "Demo PDM" --agents claude
python3 $CLI status

# ② 模拟一次真实交付：写代码 + full 档维护
echo 'class ReviewService: pass' > review.py
python3 $CLI maintain \
  --title "设计单两级审核" \
  --summary "审核漏批风险，要求主管一审后增加经理终审" \
  --implementation "审核状态机新增 manager-review 阶段，驳回统一退回待修改" \
  --business-change "设计单最终通过必须依次经过主管审核和经理审核。" \
  --change-kind added --rule-name "设计单审核流程" \
  --scenario "主管一审通过、经理二审通过才进入已通过状态；任一级驳回整单退回" \
  --domain design --changed-file review.py --validation "unit tests passed"

# ③ 业务规则演进：modified 替换而非堆积（真相层始终只有一个现行条目）
python3 $CLI maintain \
  --title "审核升级为三级" --summary "增加总监终审" --implementation "新增 director-review" \
  --business-change "设计单需依次经过主管、经理、总监三级审核。" \
  --change-kind modified --rule-name "设计单审核流程" \
  --scenario "三级依次通过才算最终通过" --domain design
cat fengchao/business-context/domains/domain-design.md   # 观察：单一现行条目 + 沿革链

# ④ 纯修复走 lite 档（零噪音）
python3 $CLI maintain --title "修复审核列表空指针" --summary "无记录时报错" --implementation "补空值判断"

# ⑤ 记录用户业务解释（含否定记忆）
python3 $CLI conversation \
  --title "审核角色边界" --domain design \
  --summary "主管指 main 岗位负责一审；经理只终审不改单" \
  --term "主管=main 岗位" \
  --rejected "不用 userId<=100 判断管理员"

# ⑥ 新会话找回记忆（有字节预算的最小集合路由）
python3 $CLI fengwang --query "设计单审核怎么改"

# ⑦ 校验与体检
python3 $CLI check --strict
python3 $CLI doctor

# ⑧ 随时停用/恢复/卸载（可逆、无残留、记忆保留）
python3 $CLI disable && git diff --stat
python3 $CLI enable
python3 $CLI uninstall && ls fengchao/
```

## 观察点

1. **步骤 ③**：`domain-design.md` 中"设计单审核流程"永远只有一个现行条目，旧版本链接进"沿革"——这是 delta 语义合并（区别于所有"追加式"记忆工具）。
2. **步骤 ④**：lite 档只产生一条 changelog，task-records 干净。
3. **步骤 ⑥**：路由结果按相关度排序、限制在 4KB 预算内、提示"先读前 3 条"。
4. **步骤 ⑧**：`disable` 后 `git diff` 只有 marker 块和薄文件消失；`uninstall` 后记忆完好。

## 录制演示动图

素材建议直接用本仓库的 dogfooding 记录（`fengchao/` 目录下是本项目自身开发的真实记忆）。
