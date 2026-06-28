# PRD — AI English Unit Studio

## 一句话定位

把每单元的英语单词表，变成女儿爱读爱听的小故事。

## 用户

- **主要用户**：用户的 13 岁大女儿，初一起，期末考试备考中。
- **次要用户**：用户的 8 岁小女儿（不适用本项目 —— 她的项目走"绘本 + 卡通风"，见 `cartoon/`）。
- **操作者**：爸爸（用户本人）—— 负责把课本词表录入系统、运行生成流水线、部署到 Vercel。

## 核心场景

1. 爸爸拍照/扫描课本每单元的生词表，转成 Excel/CSV。
2. 爸爸运行 `python scripts/run_unit.py waiyan/7a/Unit01`，流水线自动：
   - 生成嵌入全部生词的连贯故事
   - 翻译为中文
   - 为每句话生成 TTS 音频
   - 渲染成可在浏览器阅读的网页
3. 女儿在手机/电脑上打开 `https://english.hisamjo.live/waiyan/7a/Unit01/`：
   - 切换"英文 / 中文 / 对照"三种视图模式
   - 点击任意单词查中文释义
   - 听整段故事 / 逐句重听 / 调节语速
   - 当前播放的句子会高亮

## MVP 范围（v1）

✅ 在范围内：

- 词表管理（CSV → JSON）
- AI 故事生成（每个目标词在故事中至少出现 2 次）
- 中英文 / 中文 / 对照三模式切换
- 逐句 TTS 朗读 + 同步高亮
- 点击单词查中文释义（静态 ECDICT 字典）
- 响应式设计（手机 / 平板 / 电脑）

❌ 不在范围内（V2 再说）：

- 测验题（Quiz）
- 登录 / 多用户
- 学习记录 / 进度统计
- 间隔复习
- 跟读 / 发音评分
- AI 聊天
- 离线模式
- React / FastAPI / SQLite
- 多 LLM 切换

## 成功标准

**MVP 成功**：初一上 12 个单元全部跑通 `import → generate → tts → render → deploy` 流水线，部署到 `english.hisamjo.live`，女儿在手机上能流畅阅读 3 个不同单元且没有报错。

**女儿认可**：13 岁女儿主动用 1 周以上，主动点击陌生单词查释义，故事质量让她觉得"不是给小孩看的"。

## 关键决策

| 决策点 | 选择 | 理由 |
|---|---|---|
| 技术栈 | 纯 HTML + Python 脚本 | 跟 `cartoon/` 一致，零构建，部署简单 |
| LLM | `mmx text chat` (MiniMax M2.7) | settings.json 里唯一预置的 key |
| TTS | `mmx speech --voice tianxin_xiaoling` | 用户已试听认可的甜美少女声 |
| 词典 | 静态 ECDICT 嵌入 | 比 LLM 释义准，比欧路 API 不依赖外部 |
| 句数 | `max(15, round(词数 × 1.0))` | 4 词 → 15 句，50 词 → 50 句，按单元自动调 |
| 句子粒度 | 逐句 mp3（不生成整段） | 句子高亮同步零难度，Vercel 资源更小 |
| 释义生成 | 不生成（用静态字典） | LLM 释义 5% 错率对考试场景不可接受 |
| 部署 | Vercel 静态站 + hisamjo.live 子域 | 复用用户已有通道 |

## 验收清单

- [ ] Unit01 全流程跑通（vocab → story → audio → html）
- [ ] 故事中所有 24 个生词出现 ≥ 2 次
- [ ] 三个视图模式切换正常
- [ ] TTS 高亮与句子同步
- [ ] 点击 5 个不同单词都能查到释义
- [ ] 手机浏览器（iPhone Safari / Android Chrome）正常显示
- [ ] Vercel 部署到 `english.hisamjo.live` 可访问
