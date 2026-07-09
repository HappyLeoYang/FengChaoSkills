# 贡献指南

感谢关注 FengChaoSkills。开始前请先读 [docs/DESIGN.md](docs/DESIGN.md)——特别是第五部分**设计红线**，任何 PR 不得违背：

1. 运行时零第三方依赖（`fengchao.py` 只用 Python 标准库）
2. 存储只用 Markdown + Git
3. Agent 中立
4. 隐私默认 summary-only；零遥测、零网络请求
5. 用户记忆数据神圣（无显式确认不删除/改写）
6. 卸载对称性（写入的每个字节都有干净摘除路径）
7. 写入触发边界（只有真实交付写证据层）
8. 克制（工具只管格式/校验/提醒，业务判断留给 agent 和人）
9. 真相层唯一现行原则（同一规则名同一时刻只有一个现行条目）

## 开发环境

无构建、无 lint 依赖。Python 3.9+ 即可：

```bash
python3 -m unittest discover -s tests -v          # 全部测试
python3 -m unittest tests.test_fengchao_cli.DeltaMergeTests -v   # 单个测试类
```

## 代码结构须知

- **所有逻辑集中在 `skills/fengchao-business-memory/scripts/fengchao.py`**（单文件 CLI）。
- **内联模板是唯一事实源**：仓库中的 `templates/`、`adapters/` 是生成产物，勿手改。修改模板后运行：

  ```bash
  python3 skills/fengchao-business-memory/scripts/fengchao.py export-templates --out .
  ```

  CI 会校验两者一致。
- 新增诊断必须先在 `docs/DESIGN.md` 附录 C 登记 code。
- 版本号改动需同步 `fengchao.py` 的 `__version__` 与 `pyproject.toml`（CI 校验）。

## 测试约定

- 新功能一律配端到端测试：subprocess 调真实 CLI、临时目录隔离、**不 mock**。
- 纯函数（打分、合并）可直接 import 做单元测试。
- 模板措辞改动会影响测试断言，需同步更新。

## 提交规范

- 提交信息格式：`feat/fix/docs/refactor: 中文说明`。
- 本仓库 dogfooding：每次真实交付请用 `maintain` 记录到 `fengchao/`（这是活示例，也是验收要求）。

## 提问题

请用 issue 模板（bug / feature），附 `fengchao status --format json` 输出和复现步骤。
