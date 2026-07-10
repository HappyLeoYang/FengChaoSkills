---
description: FengChao：把刚才的业务解释记入记忆
---

按 conversation capture 模式从当前对话萃取用户业务解释（背景、术语、偏好、否定项）。
执行 `python3 .fengchao/skill/scripts/fengchao.py conversation --title "..." --summary "..."`（按需加 --term/--preference/--rejected）。
只保存萃取摘要，不保存完整对话；遵循 `.fengchao/skill/SKILL.md`。
