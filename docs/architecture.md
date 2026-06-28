# Architecture

## 一句话

`vocab.json` → 跑 `python scripts/run_unit.py` → 浏览器打开 `http://localhost:8765/waiyan/7a/Unit01/` → 看故事听故事查单词。

## 架构图

```
┌──────────────────────────────────────────────────────────────────────┐
│                          爸爸（用户本人）                                 │
│   拍照课本 → 整理成 CSV/Excel → 转换为 vocab.json → git push           │
└───────────────────────┬──────────────────────────────────────────────┘
                        │ 1. 提交输入
                        ▼
                ┌──────────────────┐
                │   units/         │  ← vocab.json（手填 / 脚本转换）
                │   waiyan/7a/     │
                │     Unit01/      │
                └────────┬─────────┘
                         │ 2. 跑流水线
                         ▼
            ┌────────────────────────────┐
            │  python scripts/run_unit.py │
            └────────────┬───────────────┘
                         │ 调用 mmx CLI
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ mmx text     │  │ mmx text     │  │ mmx speech   │
│ chat         │  │ chat         │  │ synthesize   │
│              │  │              │  │              │
│ 生成故事     │  │ 翻译中文     │  │ 逐句音频     │
│ story.json   │  │ story_cn.md  │  │ sent-XX.mp3  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────┬────────┴────────┬────────┘
                ▼                 ▼
        ┌──────────────────────────────┐
        │       generated/             │  ← 提交到 git
        │       waiyan/7a/Unit01/      │
        │                              │
        │  story.json (en + zh)        │
        │  audio/sent-01.mp3...        │
        │  index.html  (单单元页)      │
        └──────────────┬───────────────┘
                       │ 3. 部署（git push）
                       ▼
            ┌─────────────────────┐
            │  Vercel 静态站点     │
            │  english.hisamjo.live│
            └──────────┬──────────┘
                       │ 4. 女儿用手机/电脑访问
                       ▼
            ┌─────────────────────┐
            │  13 岁女儿          │
            │  浏览器中：         │
            │  • 切三模式         │
            │  • 点单词查释义     │
            │  • 听 TTS + 高亮    │
            └─────────────────────┘
```

## 流水线脚本

| 脚本 | 输入 | 输出 | 何时跑 |
|---|---|---|---|
| `import_vocab.py` | CSV | `vocab.json` | 每个新单元第一次 |
| `generate_story.py` | `vocab.json` | `story.json` + `meta.json` | 词表变了 |
| `generate_tts.py` | `story.json` | `audio/sent-XX.mp3` | story 变了 |
| `render.py` | `story.json` + audio | `index.html` | 任何输入变了 |
| `build_index.py` | 所有 `meta.json` | 根 `index.html` | 新增/删除单元时 |
| `run_unit.py` | 单元路径 | 全部 above | 一次性跑完 |

每个脚本都可独立重跑（idempotent），根据 `meta.json` 的 hash 决定是否跳过。

## 关键设计决策

1. **不在浏览器侧生成内容**。所有 AI / TTS 都在本地 Python 跑完，浏览器只读静态文件。这让 Vercel 部署极简（纯静态），也让女儿用手机时不会卡。

2. **句子是原子单位**。`story.json` 的 `sentences[]` 是 TTS 和 UI 的唯一边界。TTS 不用再切分句子，UI 不用再切分段落，hash 校验也不用考虑段首段尾差异。

3. **释义走静态字典**。点击单词查 ECDICT 嵌入字典（~10MB），不调 LLM。释义稳定、零延迟、零费用。

4. **mmx 是唯一外部依赖**。所有 AI / TTS 都通过 `mmx` CLI（已在 `C:\nvm4w\nodejs\mmx`）。换 LLM 只需改 `scripts/lib/mmx_text.py` 一个文件。

5. **Vercel 只承担"分发"职责**。V0 阶段 Vercel 不跑任何后端逻辑。`git push` → Vercel 自动 build（无需 build step）→ 部署静态文件。

## 性能预算

- 单元页首屏 < 500KB（HTML + CSS + JS 内联）
- 每个 mp3 ~30-80KB，24 句 ≈ 1.5MB
- 总计 < 2MB / 单元 → Vercel 100MB 限额内可放 50 个单元
- ECDICT 字典 ≈ 8MB（gzip 后）→ 一次性下载，浏览器缓存

## 安全

- 不收集任何用户数据（无登录、无 cookie、无后端）
- 静态资源只读，不写用户文件
- Vercel 部署无需环境变量（所有 key 在本地跑流水线时用）
