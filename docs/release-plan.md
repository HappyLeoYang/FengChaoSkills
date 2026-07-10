# 开源发布路线图（Release Plan）

> 版本：v1.0
> 日期：2026-07-09
> 性质：本文档是 FengChaoSkills 从"开发完成"走向"开源可用"的执行规划与交接文档。任何接手发布工作的人（或 AI 会话）应先读本文档的"背景快照"和"已定决策"，再执行各 Phase。
> 阅读顺序：`docs/DESIGN.md`（产品蓝图与实施状态）→ `CLAUDE.md`（代码架构与不变量）→ 本文档（发布执行）。

**修订记录**

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07-09 | 初版：基于 2026-07-09 与维护者的发布策略讨论，确定 GitHub 先行、插件市场后置的四阶段路线 |

---

## 一、背景快照（2026-07-09，交接必读）

### 1.1 项目状态

- 代码：v0.2.0，DESIGN.md M1–M4 全部开发任务已实现，36 个测试全绿（详见 `docs/DESIGN.md` 第七部分）。
- 分支：工作在 `develop-v2-fable`，领先 `master` 7 个提交，**尚未合并、尚未推送**。
- 远端：`origin` 目前指向 **Gitee**（`git@gitee.com:liuzhuwork/FengChaoSkills.git`），**还没有 GitHub 远端**——开源到 GitHub 是本计划的第一步，不是"推一下"就完事。
- Dogfooding：仓库自身的 `fengchao/` 下已有 1 条 implemented plan + 5 条 task-record（M1–M4 交付记录），是发布时的活示例素材。
- CI：`.github/workflows/ci.yml` 已写好但**从未跑过**（Gitee 不执行 GitHub Actions），推上 GitHub 后才有第一次真实运行。

### 1.2 已知待办的技术尾巴（发布前顺手处理）

| 项 | 位置 | 说明 |
|----|------|------|
| 占位链接替换 | `README.md`、`docs/getting-started.md`（`git clone <本仓库>`、`/path/to/FengChaoSkills`）、`examples/README.md` | 等 GitHub 仓库地址确定后统一替换为真实 URL |
| `.claude/settings.local.json` | 仓库根 | 本地权限文件，目前未被跟踪（疑似靠 `.git/info/exclude` 排除）。开源前应显式加进 `.gitignore`，避免其他贡献者误提交 |
| pyproject 缺 `[project.urls]` | `pyproject.toml` | 等 GitHub 地址确定后补 Homepage/Repository/Issues 链接 |
| README 徽章 | `README.md` | CI 首跑通过后加 CI badge、PyPI version badge |

---

## 二、已定决策记录（防止重新争论，均出自 2026-07-09 维护者讨论）

| # | 决策 | 理由 |
|---|------|------|
| 1 | **分发三通道**：① GitHub 源码直跑（基础，零门槛）② PyPI（`uvx fengchao init`，非 Claude Code 用户与 CI 场景）③ Claude Code 插件市场（Claude Code 用户主推） | 每个通道服务不同人群，互不替代 |
| 2 | **发布顺序：GitHub 先行 → 种子用户测试通过 → 才做插件市场** | 维护者明确要求：插件市场稍晚，先用真实用户验证产品 |
| 3 | **PyPI 发布用 GitHub Actions + Trusted Publishing（OIDC）** | 维护者无需本地 twine、无需管理 token；发布动作简化为"在 GitHub 点 Release" |
| 4 | **引擎保持 Python 标准库单文件** | 所有同类工具都有运行时（OpenSpec 要 Node，Spec Kit 要 uv/Python）；python3 在 Mac/Linux 出厂自带，且我们零 pip 依赖，比 `npm install -g` 还少一步。不因"看起来像主流"而改 Node |
| 5 | **插件市场版仍必须保留项目级 init** | Superpowers 装的是方法论（跟人走），FengChao 的记忆根是项目数据（跟仓库走、团队经 git 共享），插件只是分发工具本体的通道，`/fengchao:init` 在项目里创建记忆根这一步不可省 |
| 6 | **插件市场规范实现前必须重新核实**（`.claude-plugin` 清单格式、marketplace.json 结构、官方市场收录流程） | 各工具约定变动快，沿用 DESIGN.md A4 的先例：文档不预先猜测，落地时核实并把结论写进代码注释 |
| 7 | **GitHub 仓库定为 `HappyLeoYang/FengChaoSkills`**（2026-07-09 R1 执行时确定） | 全部文档占位链接与 pyproject urls 以此为准 |
| 8 | **Gitee 保留为双推镜像**：GitHub 为主远端（fetch + push），origin 追加 Gitee push URL，一条 push 同步两边 | 保留国内访问入口，对自媒体读者友好；一人维护下双推成本接近零 |
| 9 | **develop-v2-fable 以 squash 方式合入 master** | 维护者选择：master 历史保持干净，v0.2.0 以单提交呈现；完整过程历史保留在 develop-v2-fable 分支 |

---

## 三、Phase R1：GitHub 开源上线（当前阶段）

> 目标：任何人访问 GitHub 仓库，5 分钟内能装上并跑通第一次 maintain。
> 前置依赖：无。完成标志：CI 绿 + README 链接全部真实可点。

### 执行清单

1. **建 GitHub 公开仓库**（维护者操作）
   - 确定仓库名（建议 `FengChaoSkills`，与 Gitee 同名）与归属账号；
   - 不要用 GitHub 的 README/LICENSE 初始化（本地已有，避免冲突）。
2. **本地收尾提交**
   - `.gitignore` 增加 `.claude/settings.local.json`；
   - 替换 1.2 节列出的全部占位链接为真实 GitHub URL；
   - `pyproject.toml` 补 `[project.urls]`。
3. **分支与远端整理**
   - 决策点（维护者定）：`develop-v2-fable` 合入 `master` 的方式（建议 merge --no-ff 保留里程碑历史）；
   - 添加 GitHub 远端并推送（Gitee 可保留为镜像双推，或迁移后废弃——维护者定）；
   - 打 tag `v0.2.0`。
4. **CI 首跑验证**
   - 推送后确认 5 个 Python 版本矩阵全绿；
   - 已知风险：CI 冒烟步骤在 ubuntu runner 上首次运行，若 `git init` 缺省分支警告等小问题需微调 workflow。
5. **仓库门面**
   - About 描述 + topics（`ai-agent`、`claude-code`、`cursor`、`business-memory`、`developer-tools`）；
   - README 加 CI badge；
   - 开 Issues / Discussions（Discussions 用于种子用户反馈更轻量）。

### 验收

- [ ] 陌生机器 `git clone` + `python3 .../fengchao.py init` 跑通（README 路径照抄可用）
- [ ] CI 全绿
- [ ] README 无占位链接

---

## 四、Phase R2：PyPI 自动发布（可与 R1 同步准备，R1 后启用）

> 目标：`uvx fengchao init` 全球可用；此后每次发版只需在 GitHub 发 Release。
> 前置依赖：R1（Trusted Publishing 要绑定 GitHub 仓库）。

### 执行清单

1. **包名核查（第一步就做，有占用风险）**
   - 到 pypi.org 搜索 `fengchao` 是否可用；被占则备选 `fengchao-skills` / `fengchaoskills`，并同步改 `pyproject.toml` 的 `name` 与全部文档中的安装命令。
2. **PyPI 侧配置（维护者操作，一次性，约 10 分钟）**
   - 注册 PyPI 账号（建议开 2FA）；
   - Publishing → Add a new pending publisher：填 GitHub 仓库 owner/name、workflow 文件名 `release.yml`、environment 名 `pypi`。
3. **仓库侧新增 `.github/workflows/release.yml`**（开发者操作）
   - 触发：`on: release: types: [published]`；
   - 步骤：checkout → setup-python → `python -m build` → `pypa/gh-action-pypi-publish`（OIDC，无 token）；
   - `environment: pypi` + `permissions: id-token: write`。
4. **首次发布演练**
   - GitHub 上创建 Release `v0.2.0` → 观察自动发布 → 干净机器 `uvx fengchao init` 冒烟。

### 版本发布 SOP（沉淀给后续所有版本）

1. 改 `fengchao.py` 的 `__version__` 与 `pyproject.toml` 的 `version`（CI 校验二者一致）；
2. 跑 `python3 -m unittest discover -s tests`，改过模板则重跑 `export-templates --out .`；
3. 用 `maintain` 记录本次交付（dogfooding 纪律）；
4. 合并进 `master`，推送，等 CI 绿；
5. GitHub 创建 Release（tag `vX.Y.Z`，Release notes 可直接引用 `fengchao/changelog/` 记录）→ 自动上 PyPI。

### 验收

- [ ] 干净机器 `uvx fengchao init` 成功装出 `.fengchao/skill/` 完整副本并 `check` 通过（本地 wheel 已验证过等价路径，见 DESIGN.md 第七部分 M4）

---

## 五、Phase R3：种子用户测试（R1/R2 完成后，插件市场的闸门）

> 目标：3–5 个真实用户在真实项目上用两周，验证"引入无痛、无感使用、停用无残留"三个承诺。
> 完成标志达成前，**不启动 R4**（维护者明确要求）。

### 执行清单

1. **招募**：3–5 人，覆盖面要求——至少 1 个 Claude Code 用户（验证 hooks 全链路）、1 个 Cursor 用户（验证薄命令/规则通道）、1 个已有大量 CLAUDE.md 自定义内容的存量项目（验证 marker 块不打架）。维护者可从自媒体读者中招募。
2. **给用户的材料**：README Quick Start + `examples/README.md` 演示脚本 + 反馈渠道（GitHub Discussions 或微信群）。
3. **重点收集的反馈**（对应产品的核心赌注）：
   - 安装体验：几分钟装完？哪一步卡住？
   - 打扰度：stop-gate remind 是否恰到好处？有没有"烦到想关掉"（若普遍想关 → 默认档位要重新评估）；
   - maintain 心智负担：AI 自动维护的记录质量如何？`--rule-name` 稳定 key 的概念用户/AI 是否用得对（重点观察 modified 时是否乱建新规则名——`extraction-quality.md` 反模式清单的实战检验）；
   - 路由质量：新会话找回的记忆是否真的省去了重新解释业务；
   - 停用体验：有没有人试了 disable/uninstall，diff 是否如承诺般干净。
4. **问题处理**：bug 修复走正常 SOP 发 patch 版本（v0.2.x）；产品级调整（如默认 hook_mode）记入 DESIGN.md 修订。

### 退出标准（进入 R4 的闸门）

- [ ] ≥3 个用户各完成 ≥5 次真实交付的记忆维护
- [ ] 无未解决的 P0（数据丢失/损坏、卸载残留、hook 阻塞工作流）
- [ ] 至少 1 个用户确认"新会话路由回的记忆真实减少了重复解释"

---

## 六、Phase R4：Claude Code 插件市场（后置，R3 通过后启动）

> 目标：Claude Code 用户 `/plugin marketplace add <owner>/FengChaoSkills` + `/plugin install fengchao` + 项目里 `/fengchao:init` 三步可用。
> 已定架构方向见"已定决策"第 5、6 条；此处只列执行框架，细节实现时核实规范后补充。

### 执行框架

1. **核实规范**（决策 6）：`.claude-plugin/plugin.json` 与 marketplace 清单的最新格式、hooks/commands 在插件中的声明方式、插件内脚本的路径变量（如 `${CLAUDE_PLUGIN_ROOT}`）——核实结论写进插件清单文件的注释和本文档修订。
2. **插件形态设计**：插件携带 skill + 三个命令 + hooks + `fengchao.py` 引擎；新增 `/fengchao:init` 薄命令（调插件目录里的引擎在当前项目创建记忆根）。注意与项目级安装（`init` 完整模式）的共存与去重：项目里已有 `.fengchao/` 时插件命令应指向项目副本，避免版本漂移——这是实现时最需要想清楚的点。
3. **自建 marketplace 起步**：仓库内提供 marketplace 清单，用户 `marketplace add` 本仓库即可；跑顺后再申请收录 `anthropics/claude-plugins-official`（提交流程实现时核实）。
4. **文档同步**：README 的 Claude Code 安装路径切换为插件优先，`docs/getting-started.md` 增加插件章节。

---

## 七、发布配套素材（穿插进行，服务自媒体传播）

- 终端演示动图：脚本用 `examples/README.md`（八步完整生命周期），素材可直接用本仓库 dogfooding 记录；建议录 ①60 秒安装 ②added→modified 真相层单条目演进 ③disable 干净 diff 三段。
- 发布文章素材点（差异化叙事，出自 DESIGN.md 1.3）：记忆认识论分层、否定记忆、"停用无残留是同类工具集体盲区"。
- README 已含 60 秒 Quick Start 与信任声明（零依赖/零遥测/记忆归用户），可直接引用。

---

## 八、风险与开放问题

| 风险/问题 | 影响 | 预案 |
|-----------|------|------|
| PyPI 包名 `fengchao` 被占 | R2 阻塞 | 备选名 + 全文档同步改（R2 清单第 1 步优先做） |
| Windows 用户 `python3` 命令不存在（通常是 `python`/`py`） | 安装文档适用性 | R3 若有 Windows 反馈，文档补 Windows 说明；hook 命令的 `python3` 硬编码届时评估 |
| 大仓库 `git status` 慢导致 stop-gate 超 500ms | hook 体验 | 已有 `hook_mode: off` 逃生舱 + `docs/existing-projects.md` 已写明；R3 收集实际数据 |
| 插件规范变动 | R4 返工 | 决策 6：实现前核实，不预先编码 |
| Gitee/GitHub 双远端长期同步成本 | 维护负担 | 已决（2026-07-09）：双推镜像，见"已定决策"第 8 条 |
| 老布局用户升级 | 兼容 | `migrate` + `upgrade` 已就绪，发布公告注明 v0.1 → v0.2 迁移命令 |

---

## 附录：接手者速查

- **必读顺序**：`docs/DESIGN.md`（蓝图+第七部分实施状态）→ `CLAUDE.md`（架构不变量）→ 本文档。
- **核心代码**：`skills/fengchao-business-memory/scripts/fengchao.py`（唯一逻辑入口，v0.2.0）；`templates/`、`adapters/` 是生成产物勿手改。
- **测试**：`python3 -m unittest discover -s tests`（36 用例，全部端到端风格）。
- **本仓库的记忆**：`fengchao/` 目录（dogfooding），接手前可跑 `python3 skills/fengchao-business-memory/scripts/fengchao.py fengwang --query "<你的问题>"` 找回开发上下文。
- **发布纪律**：每个 Phase 的实际交付用 `maintain` 记录；每个版本按第四节 SOP 走。
