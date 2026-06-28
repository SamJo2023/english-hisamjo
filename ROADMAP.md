# ROADMAP

6 个里程碑，每个都"可独立验收"。M0 是脚手架，M5 是质量打磨。

---

## M0 — 脚手架 ✅ 进行中

**目标**：项目能跑起来，本地预览能看到占位页。

**交付**：
- [x] `README.md` — 项目说明
- [x] `PRD.md` — 产品需求
- [x] `ROADMAP.md` — 本文件
- [x] `CLAUDE.md` — 10 条开发原则
- [x] `serve.py` — 从 `cartoon/` 复制
- [x] `docs/architecture.md` — 架构图
- [x] `index.html` — 占位页
- [x] `.gitignore`

**验收**：`python serve.py` 后浏览器看到占位页。

**不在 M0**：Vercel 部署（等 M4 一起做）。

---

## M1 — 词表 + 故事生成 ⏳

**目标**：输入词表 → 自动生成嵌入所有词的英文故事 + 中文翻译。

**交付**：
- [ ] `prompts/story.system.md` — LLM 系统提示词
- [ ] `prompts/story.user.md` — LLM 用户提示词模板
- [ ] `prompts/story.schema.json` — LLM 输出 JSON schema
- [ ] `scripts/lib/mmx_text.py` — mmx text chat 封装 + 重试
- [ ] `scripts/lib/coverage.py` — 词覆盖校验（lemma + accept_forms）
- [ ] `scripts/lib/normalize.py` — 文本规范化（智能引号等）
- [ ] `scripts/lib/json_io.py` — JSON 读写工具
- [ ] `scripts/import_vocab.py` — CSV → vocab.json
- [ ] `scripts/generate_story.py` — 主入口（含 Pass-2 补足）
- [ ] `units/waiyan/7a/Unit01/vocab.json` — 24 个词手填

**验收**：`python scripts/generate_story.py waiyan/7a/Unit01` 输出 `story.json`，24 个词全部出现 ≥ 2 次，爸爸人工读一遍故事觉得质量 OK。

---

## M2 — 逐句 TTS ⏳

**目标**：每句话生成 1 个 mp3，可以单独播放。

**交付**：
- [ ] `scripts/lib/mmx_speech.py` — mmx speech synthesize 封装
- [ ] `scripts/generate_tts.py` — 逐句循环、idempotent、失败隔离
- [ ] `generated/waiyan/7a/Unit01/meta.json` — 含 hash + voice + model
- [ ] `generated/waiyan/7a/Unit01/audio/sent-01.mp3` ~ `sent-24.mp3`

**验收**：24 个 mp3 都能在播放器里正常播，文件名与 `story.json` 的句子 id 对应。

---

## M3 — 单单元 UI ⏳

**目标**：网页能切换三模式、播放音频、点击查词。

**交付**：
- [ ] 下载 ECDICT 词法子集到 `data/ecdict.csv`
- [ ] `scripts/lib/ecdict_lookup.py` — 静态字典查询
- [ ] `scripts/render.py` — 渲染 `index.html`
- [ ] `generated/waiyan/7a/Unit01/index.html` — 单单元页
  - 三模式切换（EN / CN / 双语）
  - 置底音频条（前/后/播放/进度）
  - 当前句子高亮
  - 单词点击弹卡片（lemma + 词性 + 中文 + 例句）
  - 键盘快捷键（Space 播放/暂停，J/K 上下句，F 切视图）
  - 手机端响应式

**验收**：爸爸在女儿手机上打开页面，切换模式、点 5 个单词、听 5 句话，全部正常工作。

---

## M4 — 首页 + Vercel 部署 ⏳

**目标**：`english.hisamjo.live` 公开访问。

**交付**：
- [ ] `scripts/build_index.py` — 扫描所有 `meta.json` 生成根 `index.html`
- [ ] `vercel.json` — 静态站配置
- [ ] GitHub 仓库 `SamJo2023/english-hisamjo`（需用户确认）
- [ ] Cloudflare DNS CNAME 指向 `english.hisamjo.live`（需用户确认）
- [ ] Vercel 项目 `english-hisamjo` 绑定 GitHub repo（需用户确认）

**验收**：手机访问 `https://english.hisamjo.live`，看到 Unit01 卡片，点进去正常显示。

⚠️ **部署操作前必须获得用户明确确认**（全局指令硬性要求）。

---

## M5 — 质量打磨 ⏳

**目标**：女儿主动用一周没有明显问题。

**交付**：
- [ ] 故事质量调优（如果女儿反馈"读起来怪"）
- [ ] 错误状态处理（TTS 单句失败 / LLM 返回不合法 JSON）
- [ ] 性能优化（首屏加载、音频预加载）
- [ ] README 完善

**验收**：女儿用 1 周、至少 3 个不同单元、没报错、至少主动点 10 次单词查释义。

---

## 整体进度

| 里程碑 | 状态 | 预计耗时 |
|---|---|---|
| M0 脚手架 | 🚧 进行中 | 0.5 天 |
| M1 故事生成 | ⏳ 待开始 | 1-2 天 |
| M2 TTS | ⏳ 待开始 | 1 天 |
| M3 UI | ⏳ 待开始 | 2 天 |
| M4 部署 | ⏳ 待开始 | 0.5 天 |
| M5 打磨 | ⏳ 待开始 | 1-2 天 |

**总计**：约 7-9 个工作日（M2 大部分是后台跑）。
