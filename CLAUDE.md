# CLAUDE.md — 开发规范

本项目的 10 条工作原则。每次 Claude Code 在此项目工作时必须遵守。

## 开发原则

1. **先设计，再编码**。任何新功能、重大修改前，先在 `docs/` 写设计或更新本文件，再动代码。
2. **每次只完成一个 Milestone**。M0 → M1 → M2 → M3 → M4 → M5，按顺序推进。未经用户明确同意，不跳级、不并行。
3. **不允许一次修改多个模块**。一次提交只改一个模块（如 `scripts/generate_story.py` 或 `prompts/story.system.md`），便于回滚和 review。
4. **所有 Prompt 独立存放**。LLM 提示词在 `prompts/` 下单独成文件，**绝不写死在代码里**。改 prompt 不需要改代码。
5. **所有 AI Provider 必须支持替换**。`scripts/lib/mmx_text.py` 是 LLM 调用的唯一入口，未来想换 OpenAI/Claude/Anthropic，只改这一个文件。
6. **所有生成内容必须保存到 `generated/`**。绝不写到 `units/`（输入）或临时目录。`generated/` 的内容全部提交到 git，Vercel 直接读取。
7. **代码必须模块化**。`scripts/lib/` 是可复用工具库，`scripts/*.py` 是入口。库函数无副作用、可单独测试。
8. **所有功能必须可测试**。每个脚本都能独立运行（`python scripts/xxx.py`），有可观察的输出（打印进度、生成文件、退出码 0/1）。
9. **所有配置放 `config/` 或单元的 vocab.json**。不在代码里硬编码 voice、API key、阈值。环境变量用 `os.environ.get()`，不写死。
10. **任何重大设计变更必须先输出设计方案，再等待用户确认**。包括但不限于：改数据 schema、改技术栈、改 MVP 范围、新增 V2 功能、调整部署架构。

## 与 Framework.md 的关系

本文件的前身来自 `Framework.md` 中"Claude Code 工作规范"小节。本项目**仅采纳这 10 条原则**，不采纳 Framework.md 的 React+FastAPI+SQLite 架构。

## 实施纪律

- **每个 Milestone 开始前**：在 `ROADMAP.md` 把状态从 ⏳ 改为 🚧
- **每个 Milestone 完成后**：在 `ROADMAP.md` 把状态从 🚧 改为 ✅，并附上验收记录
- **任何 prompt 调整**：单独 commit，commit message 写明改了什么、为什么
- **任何 schema 调整**：必须先 `bump schema_version` + 写迁移说明
- **任何 LLM 调用的代码改动**：必须先在 `prompts/` 测过 prompt 效果，再改调用代码

## 不在范围内（提醒）

不做的事（避免无意识扩大范围）：

- React / FastAPI / SQLite
- 多 LLM Provider 切换（v1 只接 mmx）
- 用户登录 / 账号
- 学习记录 / 间隔复习
- 测验题
- AI 聊天
- 跟读评分
- 离线模式 / Service Worker

如需做以上任何一项，**先告知用户并得到明确确认**，再开始。
