#!/usr/bin/env python3
"""渲染单元页面：单元列表 + 单故事页。

读 generated/<unit>/ 下的 story_*.json + planner.json + vocab.json
→ 写到 generated/<unit>/index.html + story_<id>.html
→ 同时更新根 index.html

用法：
  python scripts/render.py waiyan/7a/Unit01
  python scripts/render.py --all
"""
import argparse
import json
import re
import sys
from pathlib import Path

# UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))
from lib.json_io import read_json  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"


# ---------- 文本处理 ----------

# 简单后缀剥离（用于 click-to-translate 时的"近似匹配"）
_SUFFIXES = ["'s", "s", "ed", "d", "ing", "er", "est", "ly"]


def tokenize_with_vocab(en_text: str, vocab_lemmas: set[str]) -> str:
    """把英文句子切分成 HTML，词表里的词用 <span class="word" data-lemma> 包起来。

    简单实现：\b 词边界匹配 + 后缀剥离回原形。
    """
    def repl(match: re.Match) -> str:
        word = match.group(0)
        lemma = match.group(1)  # 字母部分（不含末尾标点）
        trailing = match.group(2)  # 末尾标点
        # 查 vocab：原形 OR 剥离后缀的形
        if lemma.lower() in vocab_lemmas:
            return f'<span class="word" data-lemma="{lemma.lower()}">{lemma}</span>{trailing}'
        # 试剥离后缀
        candidate = lemma.lower()
        for suf in _SUFFIXES:
            if candidate.endswith(suf) and len(candidate) > len(suf) + 1:
                stem = candidate[: -len(suf)]
                if stem in vocab_lemmas:
                    return f'<span class="word" data-lemma="{stem}">{lemma}</span>{trailing}'
        return word

    # 匹配：英文/数字组成的词 + 末尾标点
    pattern = re.compile(r"([A-Za-z][A-Za-z'-]*)([.,!?;:\"]*)")
    return pattern.sub(repl, en_text)


def render_story_html(story: dict, vocab: list[dict], audio_base: str, theme: dict | None = None) -> str:
    """渲染单个故事的 HTML 页面。

    Args:
        story: story_*.json 内容（含 _meta）
        vocab: 该故事的目标词列表
        audio_base: 相对 audio 目录的路径
        theme: 来自 planner 的 theme dict（含 theme_class 等）。review 故事传
            planner["review"]，普通故事传 planner["themes"][i]。若为 None
            （如 Unit01 旧数据），fallback 到 hardcoded mapping。
    """
    template = (TEMPLATES_DIR / "story.html").read_text(encoding="utf-8")
    vocab_lemmas = set(w["lemma"].lower() for w in vocab)

    # 主题 → CSS class 映射
    # 优先从 planner 的 theme.theme_class 字段读（Unit02+ 的新约定）；
    # 缺省时 fallback 到 hardcoded dict（Unit01 兼容，planner.json 没这字段）
    theme_id = story["_meta"]["theme_id"]
    theme_class = (theme or {}).get("theme_class")
    if not theme_class:
        theme_class = {
            # Unit01 legacy（2026-06-30 之前的 planner.json 没 theme_class 字段）
            "magical-chocolate-factory": "chocolate",
            "kind-barber": "barber",
            "orpheus-mystery": "mystery",
            "harsh-winter": "winter",
        }.get(theme_id, "chocolate")

    # Cover 图作 hero 背景（如果存在）。路径相对 story_*.html 4 层 ../ 到项目根
    # cover_id 优先于 theme_id（planner 可指定 cover_id override，给同 theme_id 的
    # 不同单元用不同封面，例如 Unit02 review 和 Unit03 review 都 theme_id="review"，
    # 但 Unit03 通过 review.cover_id="unit03-review" 指向专属封面）
    cover_id = (theme or {}).get("cover_id") or theme_id
    cover_path = REPO_ROOT / "data" / "covers" / f"{cover_id}.png"
    if cover_path.exists():
        # HTML attribute 中 URL 里的单引号要转义。这里用 CSS url()，外层用双引号
        hero_class = " has-cover"
        hero_style = f' style="background-image: url(\'../../../../data/covers/{cover_id}.png\');"'
    else:
        hero_class = ""
        hero_style = ""

    # 渲染三种 view
    en_html = render_section(story, vocab_lemmas, mode="en")
    zh_html = render_section(story, vocab_lemmas, mode="zh")
    bi_html = render_section(story, vocab_lemmas, mode="bilingual")

    n = len(story["sentences"])
    voice_label = "天心小灵"
    # 单词音频路径：相对于 generated/<unit>/story_*.html
    # 故事 HTML 在 generated/waiyan/7a/Unit01/ 4 层深 → 要 4 个 .. 才能回项目根
    word_audio_base = "../../../../data/word_audio/"
    return (template
        .replace("{{THEME_CLASS}}", theme_class)
        .replace("{{HERO_CLASS}}", hero_class)
        .replace("{{HERO_STYLE_ATTR}}", hero_style)
        .replace("{{TITLE_EN}}", story.get("title_en", ""))
        .replace("{{TITLE_ZH}}", story.get("title_zh", ""))
        .replace("{{UNIT_TITLE_ZH}}", story["_meta"].get("theme_name_zh", ""))
        .replace("{{N_SENTENCES}}", str(n))
        .replace("{{N_WORDS}}", str(len(vocab)))
        .replace("{{N_SENTENCES_PADDED}}", str(n).zfill(2))
        .replace("{{VOICE_LABEL}}", voice_label)
        .replace("{{EN_SENTENCES_HTML}}", en_html)
        .replace("{{ZH_SENTENCES_HTML}}", zh_html)
        .replace("{{BILINGUAL_SENTENCES_HTML}}", bi_html)
        .replace("{{STORY_JSON}}", json.dumps(story, ensure_ascii=False))
        .replace("{{VOCAB_JSON}}", json.dumps(vocab, ensure_ascii=False))
        .replace("{{AUDIO_BASE_JSON}}", json.dumps(audio_base, ensure_ascii=False))
        .replace("{{WORD_AUDIO_BASE_JSON}}", json.dumps(word_audio_base, ensure_ascii=False))
    )


def render_section(story: dict, vocab_lemmas: set[str], mode: str) -> str:
    """渲染一个 view 模式（en / zh / bilingual）的句子 HTML。"""
    parts = []
    for i, sent in enumerate(story["sentences"], 1):
        badge = f'<span class="sent-badge">{i}</span>'
        content = f'<span class="sent-content">'
        if mode == "en":
            en_with_words = tokenize_with_vocab(sent["en"], vocab_lemmas)
            content += f'<span class="sent-en">{en_with_words}</span>'
        elif mode == "zh":
            content += f'<span class="sent-zh">{sent["zh"]}</span>'
        elif mode == "bilingual":
            en_with_words = tokenize_with_vocab(sent["en"], vocab_lemmas)
            content += (
                f'<span class="sent-en">{en_with_words}</span>'
                f'<span class="sent-zh">{sent["zh"]}</span>'
            )
        content += '</span>'
        parts.append(f'<div class="sentence" data-sent="{sent["id"]}">{badge}{content}</div>')
    return "\n        ".join(parts)


def render_unit_index_html(unit_path: str, vocab: dict, planner: dict, story_files: list[Path]) -> str:
    """渲染单元首页（Hero + 4 个故事卡片）。"""
    template = (TEMPLATES_DIR / "unit.html").read_text(encoding="utf-8")

    # 计算 cover 路径：unit HTML 在 generated/waiyan/7a/Unit01/ 4 层深 → 4 个 ../
    cover_base = "../../../../data/covers/"

    # Hero 用第一个主题的封面
    first_theme_id = planner.get("themes", [{}])[0].get("id", "magical-chocolate-factory")
    hero_cover = cover_base + first_theme_id + ".png"

    # 年级标签
    grade_label = {"7a": "初一上", "7b": "初一下", "8a": "初二上", "8b": "初二下"}.get(
        vocab.get("grade", ""), vocab.get("grade", "")
    )

    cards = []
    total_words = sum(len(t["word_list"]) for t in planner.get("themes", []))
    total_words += len(planner.get("review", {}).get("word_list", []))

    for sf in story_files:
        story = read_json(sf)
        is_review = story["_meta"].get("is_review", False)
        theme_id = story["_meta"]["theme_id"]
        # 取 theme dict（用于 cover_id override）
        if is_review:
            theme_dict = planner.get("review", {})
        else:
            theme_dict = next((t for t in planner.get("themes", []) if t.get("id") == theme_id), {}) or {}
        cover_id = theme_dict.get("cover_id") or theme_id
        tag_class = "review" if is_review else ""
        tag_text = "复习 REVIEW" if is_review else "主题 STORY"
        cover = cover_base + cover_id + ".png"
        n_unused = len(story["_meta"].get("coverage", {}).get("missing", []))
        # 根绝对路径：避免 cleanUrls + 浏览器相对解析导致目录丢失
        story_href = f"/generated/{unit_path}/{sf.stem}.html"
        cards.append(
            f'<a class="story-card" href="{story_href}" style="--card-bg: url(\'{cover}\')">'
            f'<div class="play-icon">▶</div>'
            f'<div class="story-card-content">'
            f'<span class="story-tag {tag_class}">{tag_text}</span>'
            f'<div class="story-title-zh">{story.get("title_zh","")}</div>'
            f'<div class="story-title-en">{story.get("title_en","")}</div>'
            f'<div class="story-info">🎧 {len(story["sentences"])} 句</div>'
            f'</div>'
            f'</a>'
        )

    return (template
        .replace("{{ROOT_INDEX_PATH}}", "../../../../index.html")
        .replace("{{HERO_COVER}}", hero_cover)
        .replace("{{UNIT_TITLE_ZH}}", vocab.get("unit_title_zh", ""))
        .replace("{{UNIT_TITLE_EN}}", vocab.get("unit_title_en", ""))
        .replace("{{UNIT_THEME_EN}}", vocab.get("unit_theme_en", ""))
        .replace("{{UNIT_THEME_ZH}}", vocab.get("unit_theme_zh", ""))
        .replace("{{UNIT_THEME_DISPLAY}}", _unit_theme_display(vocab))
        .replace("{{HERO_THEME_HTML}}", _hero_theme_html(vocab))
        .replace("{{GRADE_LABEL}}", grade_label)
        .replace("{{N_THEMES}}", str(len(planner.get("themes", [])) + (1 if planner.get("review", {}).get("word_list") else 0)))
        .replace("{{TOTAL_WORDS}}", str(total_words))
        .replace("{{STORY_CARDS_HTML}}", "\n    ".join(cards))
    )


def _unit_theme_display(vocab: dict) -> str:
    """组装 unit theme 在 hero 上的显示：'Go for it! · 去挑战！'。无则返回空串。"""
    en = vocab.get("unit_theme_en", "")
    zh = vocab.get("unit_theme_zh", "")
    if en and zh:
        return f"{en} · {zh}"
    return en or zh


def _hero_theme_html(vocab: dict) -> str:
    """渲染 hero 里 unit theme 的 HTML 块。空则返回空串（UI 上不占位）。"""
    display = _unit_theme_display(vocab)
    if not display:
        return ""
    return (
        f'<div class="hero-theme">'
        f'<span class="hero-theme-label">UNIT THEME</span>'
        f'<span class="hero-theme-text">{display}</span>'
        f'</div>'
    )


def render_root_index_html(units: list[dict]) -> str:
    """渲染根 index.html（单元列表，每个单元卡片带封面）。"""
    template = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")

    # 找每个单元的 plan + 第 1 个主题的 cover
    cards = []
    for u in units:
        planner_path = REPO_ROOT / u["path"] / "planner.json"
        cover_url = "data/covers/magical-chocolate-factory.png"  # 兜底
        if planner_path.exists():
            try:
                planner = read_json(planner_path)
                themes = planner.get("themes", [])
                if themes:
                    first_id = themes[0].get("id", "magical-chocolate-factory")
                    cover_url = f"data/covers/{first_id}.png"
            except Exception:
                pass

        # grade 标签
        grade_label = {"7a": "初一上", "7b": "初一下", "8a": "初二上", "8b": "初二下"}.get(u.get("grade", ""), u.get("grade", ""))

        cards.append(
            f'<a class="unit-card" href="{u["path"]}/index.html" style="--card-bg: url(\'{cover_url}\')">'
            f'<div class="unit-arrow">→</div>'
            f'<div class="unit-card-content">'
            f'<span class="unit-card-tag">📖 {grade_label} · 外研社</span>'
            f'<div class="unit-title-en">{u["title_en"]}</div>'
            f'<div class="unit-title-zh">{u["title_zh"]}</div>'
            f'<div class="unit-meta"><span>🎙 {u["n_themes"]} 个故事</span></div>'
            f'</div>'
            f'</a>'
        )
    return template.replace("{{UNIT_CARDS_HTML}}", "\n    ".join(cards))


# ---------- 主流程 ----------

def render_unit(unit_path: str, force: bool):
    """渲染一个单元的所有 HTML。"""
    unit_dir = REPO_ROOT / "generated" / unit_path
    if not unit_dir.exists():
        print(f"❌ 单元目录不存在：{unit_dir}", file=sys.stderr)
        return False

    vocab_path = REPO_ROOT / "units" / unit_path / "vocab.json"
    if not vocab_path.exists():
        print(f"❌ 词表不存在：{vocab_path}", file=sys.stderr)
        return False

    vocab = read_json(vocab_path)
    planner = read_json(unit_dir / "planner.json")
    story_files = sorted(unit_dir.glob("story_*.json"))
    if not story_files:
        print(f"❌ 没有 story_*.json：{unit_dir}", file=sys.stderr)
        return False

    print(f"\n📐 渲染单元：{unit_path}")
    print(f"   {len(story_files)} 个故事")

    # 为每个 story 渲染 HTML
    for sf in story_files:
        story = read_json(sf)
        theme_id = story["_meta"]["theme_id"]
        # 取该 story 的词 + 完整 theme dict（render_story_html 需要 theme_class）
        if story["_meta"].get("is_review"):
            theme_dict = planner.get("review", {})
            word_lemmas = set(theme_dict.get("word_list", []))
        else:
            theme_dict = next((t for t in planner["themes"] if t["id"] == theme_id), None) or {}
            word_lemmas = set(theme_dict.get("word_list", []))
        words = [w for w in vocab["words"] if w["lemma"].lower() in {l.lower() for l in word_lemmas}]

        out_html = unit_dir / f"{sf.stem}.html"
        if out_html.exists() and not force:
            print(f"  ⏭️  {out_html.name} 已存在")
            continue

        # audio base 路径：相对 HTML 文件位置
        audio_base = f"audio/{theme_id}/"
        html = render_story_html(story, words, audio_base, theme=theme_dict)
        out_html.write_text(html, encoding="utf-8")
        print(f"  ✓ {out_html.name}（{len(words)} 词，{len(story['sentences'])} 句）")

    # 单元首页
    unit_index = unit_dir / "index.html"
    if not unit_index.exists() or force:
        html = render_unit_index_html(unit_path, vocab, planner, story_files)
        unit_index.write_text(html, encoding="utf-8")
        print(f"  ✓ {unit_index.name}（单元首页）")
    else:
        print(f"  ⏭️  {unit_index.name} 已存在")

    return True


def render_root_index(force: bool):
    """扫描所有 generated/*/*/Unit*/ 重新生成根 index.html。"""
    units = []
    for unit_dir in sorted((REPO_ROOT / "generated").glob("*/[78]*/*")):
        planner = unit_dir / "planner.json"
        vocab_src = REPO_ROOT / "units" / unit_dir.relative_to(REPO_ROOT / "generated") / "vocab.json"
        if not planner.exists() or not vocab_src.exists():
            continue
        planner_data = read_json(planner)
        vocab_data = read_json(vocab_src)
        n_themes = len(planner_data.get("themes", []))
        if planner_data.get("review", {}).get("word_list"):
            n_themes += 1
        # 用 as_posix() 强制正斜杠（URL 必须是正斜杠，Windows 反斜杠在浏览器和 Vercel 都会 404）
        rel_path = unit_dir.relative_to(REPO_ROOT).as_posix()
        units.append({
            "path": rel_path,
            "title_en": vocab_data.get("unit_title_en", ""),
            "title_zh": vocab_data.get("unit_title_zh", ""),
            "textbook": vocab_data.get("textbook", ""),
            "grade": vocab_data.get("grade", ""),
            "n_themes": n_themes,
        })

    if not units:
        print("⚠️  没有可渲染的单元")
        return

    index_path = REPO_ROOT / "index.html"
    if index_path.exists() and not force:
        print(f"⏭️  根 index.html 已存在")
        return

    html = render_root_index_html(units)
    index_path.write_text(html, encoding="utf-8")
    print(f"  ✓ 根 index.html（{len(units)} 个单元）")


def main():
    ap = argparse.ArgumentParser(description="渲染 HTML 页面")
    ap.add_argument("unit_path", nargs="?", help="单元路径（不传则只渲染根 index）")
    ap.add_argument("--all", action="store_true", help="渲染所有单元")
    ap.add_argument("--force", action="store_true", help="强制重生成")
    args = ap.parse_args()

    if args.all:
        for unit_dir in sorted((REPO_ROOT / "generated").glob("*/[78]*/*")):
            render_unit(str(unit_dir.relative_to(REPO_ROOT)), args.force)
        render_root_index(args.force)
    elif args.unit_path:
        render_unit(args.unit_path, args.force)
        render_root_index(args.force)
    else:
        render_root_index(args.force)

    print(f"\n✅ 渲染完成。本地预览：python serve.py")


if __name__ == "__main__":
    main()
