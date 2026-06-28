# AI English Unit Studio

把英语课本（外研版）每单元的单词表，变成一篇**可读、可听、可查**的小故事，帮你 13 岁的女儿通过阅读和听力自然掌握单词，比死背词表更高效。

**在线访问**：<https://english.hisamjo.live>（待部署）

**目标用户**：13 岁初一女生，期末考试备考中。

**MVP 范围**：3 件事 —— ① 词表管理 ② AI 故事生成 ③ 英文/中文/对照三模式切换 + 逐句 TTS 朗读 + 点击单词查释义

**当前状态**：M0 脚手架阶段。详见 [ROADMAP.md](ROADMAP.md) 和 [PRD.md](PRD.md)。

## 本地预览

```bash
cd D:\zhouxiping\16_claudecode\englisharticlePractice
python serve.py
# 浏览器打开 http://localhost:8765
```

`serve.py` 是从 `cartoon/` 项目复制的 UTF-8 编码修复版，Windows 中文路径下也能正确处理。

## 项目结构

```
englisharticlePractice/
├── README.md, PRD.md, ROADMAP.md, CLAUDE.md
├── serve.py                  # 本地静态服务器
├── units/                    # 输入：手工整理的单元词表
├── generated/                # 输出：AI 生成的单元内容（提交到 git）
├── prompts/                  # LLM 提示词（独立文件管理）
├── scripts/                  # 构建流水线（Python）
├── docs/                     # 架构、prompt 设计、数据模型、部署文档
└── data/                     # 静态资源（如 ECDICT 英汉词典子集）
```

## 技术栈

- **前端**：纯 HTML + 原生 JS + CSS，零构建
- **生成流水线**：本地 Python 3 脚本，调用 `mmx` CLI
- **AI 模型**：`mmx text chat` (MiniMax M2.7)
- **TTS**：`mmx speech synthesize --voice tianxin_xiaoling`
- **词典**：嵌入式 ECDICT 静态字典（MIT，76 万词英汉）
- **存储**：纯文件系统（JSON + mp3）
- **部署**：Vercel 静态站点，git push 自动部署到 `english.hisamjo.live`

## 与 Framework.md 的关系

项目根目录有一份 [Framework.md](Framework.md)，是 ChatGPT 生成的初版草案（React + FastAPI + SQLite 架构）。本项目**未采用**那套架构 —— 改用 plain HTML + 本地 Python 脚本，更轻量、复用 `cartoon/` 项目已验证的模式。详细对比见 [docs/architecture.md](docs/architecture.md)。

## 详细文档

- [PRD.md](PRD.md) — 产品需求
- [ROADMAP.md](ROADMAP.md) — 6 个里程碑
- [CLAUDE.md](CLAUDE.md) — 开发规范（10 条原则）
- [docs/architecture.md](docs/architecture.md) — 架构图与说明
- [plan](C:\Users\zhou.xi.ping\.claude\plans\replicated-singing-spark.md) — 完整方案（含与 Framework.md 对比）
