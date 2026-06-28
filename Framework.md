我很赞同你的想法，而且根据这几天我们聊 Claude Code 的内容，我觉得这个项目甚至比 SAP 测试执行引擎更适合作为 Claude Code 的长期项目。

原因是它的需求稳定、模块清晰，而且以后可以不断增加 Skill。

**如果让我做，我不会把它定义为"英语学习网站"，而是定义为：**

> **AI English Unit Studio（AI 单元学习助手）**

Slogan：

Generate a complete English learning unit with AI.

网站只是它的一个展示层。

下面这个项目骨架，我会直接作为 Claude Code 的 Project README（或者 PRD.md）使用，让它作为整个项目的最高指导文档。

---

# AI English Learning Platform（项目骨架）

```text
AI English Learning Platform
│
├── README.md                  # 项目介绍
├── PRD.md                     # 产品需求
├── ROADMAP.md                 # 开发计划
├── CLAUDE.md                  # Claude Code 工作规范
│
├── docs/
│   ├── architecture.md
│   ├── prompt-design.md
│   ├── database.md
│   ├── api.md
│   └── ui-design.md
│
├── frontend/
│
├── backend/
│
├── database/
│
├── prompts/
│
├── skills/
│
├── units/
│
├── generated/
│
└── tests/
```

---

# PRD（产品定位）

## 一、项目目标

开发一个 AI 驱动的英语学习平台。

用户输入：

* 一个单元的新单词
* 年级
* 教材版本

AI 自动生成完整学习内容。

目标不是背单词。

目标是：

> **让孩子通过阅读、听力、练习自然掌握单词。**

---

# MVP（第一版）

第一版只完成下面流程：

```text
输入：

Unit05

elephant
forest
river
afraid
together

↓

AI

↓

Story

↓

Chinese

↓

Bilingual

↓

Quiz

↓

HTML

↓

MP3
```

只要完成这个流程，就算成功。

---

# 后续版本

以后再增加：

✅ 登录

✅ 学习记录

✅ 错题本

✅ AI聊天

✅ Shadowing

✅ 跟读评分

这些全部属于 V2。

---

# 功能模块

建议拆成下面几个 Skill。

---

## Story Skill

职责：

根据单词生成故事。

输入：

```text
年级

教材版本

Unit

Vocabulary
```

输出：

```text
story.md
```

要求：

* 必须包含所有单词
* 每个单词至少出现2次
* 文章长度可配置
* 阅读难度可配置

---

## Translation Skill

输入：

```text
story.md
```

输出：

```text
story_cn.md

story_bilingual.md
```

要求：

支持：

英文

中文

中英对照

---

## Vocabulary Skill

负责：

统计：

每个单词：

出现次数

词性

音标

中文

例句

输出：

```text
words.json
```

---

## Quiz Skill

根据故事自动生成：

选择题

填空题

判断题

阅读理解

输出：

```text
quiz.json
```

---

## TTS Skill

根据 story.md：

生成：

```text
story.mp3
```

以后支持：

多个声音

多个语速

英音

美音

---

## HTML Skill

根据所有内容：

生成：

```text
index.html
```

页面支持：

English

Chinese

Bilingual

Play

Quiz

Words

---

# 数据目录

建议这样设计。

```text
units/

    Grade3/

        Unit01/

            vocab.txt

            config.json

        Unit02/

        Unit03/

    Grade4/

    Grade5/
```

---

生成内容：

```text
generated/

    Grade3/

        Unit01/

            story.md

            story_cn.md

            story_bilingual.md

            quiz.json

            words.json

            story.mp3

            index.html
```

以后所有资源统一放这里。

---

# Prompt 管理

这是整个项目最重要的部分。

建议：

```text
prompts/

    story.md

    translate.md

    quiz.md

    words.md

    tts.md
```

所有 Prompt 独立管理。

不要写死在代码里面。

以后改 Prompt 不需要改代码。

---

# 技术架构

建议：

```text
Frontend

React

↓

Backend

FastAPI

↓

SQLite

↓

LLM

↓

OpenAI

Claude

Gemini

（可切换）
```

所有 AI Provider：

统一接口。

以后更换模型：

无需修改业务代码。

---

# 页面规划

首页：

```text
选择：

年级

↓

教材

↓

Unit

↓

开始学习
```

学习页：

```text
标题

↓

播放按钮

↓

English

↓

Chinese

↓

Bilingual

↓

Words

↓

Quiz
```

非常简单。

不要一开始就做复杂 UI。

---

# Claude Code 工作规范（CLAUDE.md）

这里我建议写清楚，让 Claude Code 每次都遵守。

```markdown
开发原则：

1、先设计，再编码。

2、每次只完成一个 Milestone。

3、不允许一次修改多个模块。

4、所有 Prompt 独立存放。

5、所有 AI Provider 必须支持替换。

6、所有生成内容必须保存到 generated。

7、代码必须模块化。

8、所有功能必须可测试。

9、所有配置放 config。

10、任何重大设计变更必须先输出设计方案，再等待确认。
```

---

# Roadmap

建议拆成 10 个里程碑。

```text
Milestone 1

项目初始化

====================

Milestone 2

Story Generator

====================

Milestone 3

Translation

====================

Milestone 4

Vocabulary

====================

Milestone 5

Quiz

====================

Milestone 6

TTS

====================

Milestone 7

HTML

====================

Milestone 8

Web UI

====================

Milestone 9

Database

====================

Milestone 10

Learning Record
```

---

## 我建议再增加一个"内容质量控制"模块

这是我看完整个项目后觉得**最值得投入精力**的地方，也是未来真正决定这个项目价值的核心，而不是 UI。

可以新增一个 **Content Quality Skill**：

```text
Content Quality Skill

↓

检查：

✓ 是否包含所有新词

✓ 每个新词是否至少出现2~3次

✓ 是否符合对应年级阅读难度

✓ 是否包含本单元重点句型

✓ 是否存在超纲词汇（可配置比例）

✓ 故事情节是否连贯

↓

输出：

quality_report.json

↓

只有通过检查才进入下一步（翻译、TTS、HTML）
```

这样，整个流程就从"AI 生成内容"升级为"AI 生成 + AI 自检"，大幅提高生成内容的稳定性。对于你这样喜欢搭建可持续工作流的人来说，这会比一开始追求炫酷界面更有长期价值，也更符合你之前设计 SAP 测试执行引擎时强调的"先搭好引擎，再不断增加 Skill"的思路。
