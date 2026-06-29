# ROADMAP

6 个里程碑，每个都"可独立验收"。M0 是脚手架，M5 是质量打磨。

---

## M0 — 脚手架 ✅

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

## M1 — 词表 + 故事生成 ✅

**目标**：输入词表 → 按 Curriculum Planner 分主题 → 生成 4 个故事。

**交付**：
- [x] `prompts/{story,planner}.{system,user,schema}.md` — LLM 提示词（multi-story 模式）
- [x] `scripts/lib/{mmx_text,coverage,normalize,json_io}.py`
- [x] `scripts/import_vocab.py` — md/csv → vocab.json
- [x] `scripts/plan_curriculum.py` — vocab → planner.json（按主题分组）
- [x] `scripts/generate_story.py` — 主入口（含 Pass-2 补足 + --all 默认 4 故事）
- [x] `units/waiyan/7a/Unit01/vocab.json` — 46 词
- [x] `generated/waiyan/7a/Unit01/{planner.json, story_*.json, story_*.html}` — 4 故事

**验收**：`python scripts/generate_story.py waiyan/7a/Unit01 --all` 输出 4 个 story_*.json，质量人工 review OK（multi-story per theme 模式，每单元 3 主题 + 1 复习）。

---

## M2 — 逐句 TTS ✅

**目标**：每句话生成 1 个 mp3，可单独播放。

**交付**：
- [x] `scripts/lib/mmx_speech.py` — mmx speech synthesize 封装
- [x] `scripts/generate_tts.py` — 逐句循环、idempotent、失败隔离
- [x] `scripts/generate_word_audio.py` — 单词级发音（点击查词弹窗用）
- [x] `generated/waiyan/7a/Unit01/audio/<theme>/sent-*.mp3` — 共 45 个句子 mp3
- [x] `data/word_audio/<lemma>.mp3` — 46 个单词 mp3

**验收**：所有 mp3 可在播放器正常播，文件名与 `story_*.json` 的句子 id 对应。`mmx tts_failures` 为空。

---

## M3 — 单单元 UI ✅

**目标**：网页能切换三模式、播放音频、点击查词。

**交付**：
- [x] `scripts/render.py` — 渲染单元 index.html + 4 个 story_*.html（4 主题色 + hero + 动画）
- [x] `generated/waiyan/7a/Unit01/index.html` — 单单元页
  - [x] 4 故事卡片 + 主题色
  - [x] 故事页：三模式切换（EN / CN / 双语）
  - [x] 置底音频条（前/后/播放/进度条可点击 seek）
  - [x] 当前句子高亮 + 播放脉冲动画
  - [x] 单词点击弹卡片（lemma + 词性 + 中文 + 音标 + 单词发音）
  - [x] 键盘快捷键（Space 播放/暂停，J/K 上下句，F 切视图）
  - [x] 手机端响应式
- [x] `templates/{index,unit,story}.html` — 渲染模板
- [x] **inline VOCAB 数组**到 story_*.html（点查词用本单元 vocab 的 gloss_zh）—— **不是 plan 里说的 ECDICT**

**验收**：女儿在手机浏览器打开页面，切换模式、点 5 个单词、听 5 句话、查看单词发音，全部正常工作。**点查词仅支持本单元目标词；非目标词（连接词、专有名词等）点不动**（这是有意的简化，不是 bug）。

---

## M4 — 首页 + Vercel 部署 ✅

**目标**：`english.hisamjo.live` 公开访问。

**交付**：
- [x] `vercel.json` — 静态站配置（cleanUrls, no trailingSlash）
- [x] `index.html`（根）— 单元卡片列表（手写，可选自动化见下）
- [x] GitHub 仓库 `SamJo2023/english-hisamjo`（public）
- [x] Cloudflare DNS CNAME `english → cname.vercel-dns.com`（proxied，SSL=Full）
- [x] Vercel 项目 `english-hisamjo`（team `sam-jos-projects`）部署上线
- [x] Vercel ↔ GitHub 链接已建：`git push` 自动部署
- [~] `scripts/build_index.py` — **跳过**（用户决策：根 index.html 手写，V2 再说）

**验收**：手机访问 `https://english.hisamjo.live`，看到 Unit01 卡片，点进去 4 个故事都能正常打开。✅ 2026-06-29 端到端验证通过。

⚠️ **部署操作前必须获得用户明确确认**（全局指令硬性要求）—— 本次部署已遵守。

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

| 里程碑 | 状态 | 实际耗时 | 备注 |
|---|---|---|---|
| M0 脚手架 | ✅ | 0.5 天 | serve.py 从 cartoon/ 复制 |
| M1 故事生成 | ✅ | 2 天 | 比预期多了 multi-story 重构（reference-suggestion1） |
| M2 TTS | ✅ | 1 天 | 加了 generate_word_audio 单词级发音 |
| M3 UI | ✅ | 2 天 | 4 主题色 + hero + 动画，比 plan 复杂 |
| M4 部署 | ✅ | 1 天 | CLI 直传（公司网封了 git push）+ redeploy 修了一次 edge 缓存 |
| M5 打磨 | ⏳ 等女儿验收 | — | 用 1 周后再开 |

**总计**：约 6.5 个工作日（M0-M4）。M5 等真实使用反馈。
