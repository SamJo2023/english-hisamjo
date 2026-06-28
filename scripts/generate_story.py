#!/usr/bin/env python3
"""AI 故事生成主入口（主题模式）。

读 vocab.json + planner.json → 取某个 theme 的词 → 调 mmx text chat →
校验 → 写到 generated/.../story_<theme_id>.json

支持 3 种模式：
- 主题模式（推荐）：--theme <id>  生成某个主题的短故事
- 复习模式：        --review      生成 review 主题的兜底短故事
- 传统模式（向后兼容）：无 flag 时，从全部词生成一个 story.json

特性：
- 严格 JSON 输出，自动重试解析
- Pass-2 补足：对覆盖不足的词再次调用 LLM 让其补足
- 失败时不静默通过：覆盖不达标则 exit 1
- meta.json 写 hash，支持 idempotent 重跑

用法：
  python scripts/generate_story.py waiyan/7a/Unit01 --theme magical-chocolate-factory
  python scripts/generate_story.py waiyan/7a/Unit01 --review
  python scripts/generate_story.py waiyan/7a/Unit01 --all    # 跑所有主题
  python scripts/generate_story.py waiyan/7a/Unit01 --theme <id> --force
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path  # noqa: E402

# UTF-8 输出
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# 允许 import lib
sys.path.insert(0, str(Path(__file__).parent))
from lib.json_io import read_json, write_json  # noqa: E402
from lib.mmx_text import chat_json  # noqa: E402
from lib.coverage import check_coverage, format_report  # noqa: E402
from lib.normalize import normalize_text  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"


def load_prompts() -> tuple[str, str]:
    system = (PROMPTS_DIR / "story.system.md").read_text(encoding="utf-8")
    user_tmpl = (PROMPTS_DIR / "story.user.md").read_text(encoding="utf-8")
    return system, user_tmpl


def render_user_prompt(user_tmpl: str, *,
                        theme_name_zh: str, theme_name_en: str,
                        scene_description: str, character_focus: list[str],
                        words: list[dict], target_sentences: int) -> str:
    word_list_lines = [f"- {w['lemma']} [{w['pos']}] — {w['gloss_zh']}" for w in words]
    return (user_tmpl
        .replace("{{theme_name_zh}}", theme_name_zh)
        .replace("{{theme_name_en}}", theme_name_en)
        .replace("{{scene_description}}", scene_description)
        .replace("{{character_focus}}", ", ".join(character_focus) if character_focus else "（无指定）")
        .replace("{{word_count}}", str(len(words)))
        .replace("{{word_list}}", "\n".join(word_list_lines))
        .replace("{{target_sentences}}", str(target_sentences))
    )


def validate_story(story: dict, words_subset: list[dict], target_sentences: int) -> tuple[dict, dict]:
    """校验 LLM 输出的 story。返回 (story, coverage)。"""
    actual_n = len(story["sentences"])
    if actual_n != target_sentences:
        if actual_n > target_sentences:
            story["sentences"] = story["sentences"][:target_sentences]
        else:
            print(f"  ⚠️  LLM 少生成 {target_sentences - actual_n} 句（coverage 仍会算）")

    for i, sent in enumerate(story["sentences"], 1):
        sent["id"] = f"s{i:02d}"
        sent["en"] = normalize_text(sent["en"])
        sent["zh"] = normalize_text(sent["zh"])

    coverage = check_coverage(words_subset, [s["en"] for s in story["sentences"]], min_occurrences=1)
    return story, coverage


def regenerate_for_missing(story, words_subset, system, coverage):
    """Pass-2 补足。"""
    problems = coverage["missing"] + [l for l, _ in coverage["under_covered"]]
    if not problems:
        return story

    print(f"  🔄 Pass-2 补足：{len(problems)} 个词未达标")
    for lemma, c in coverage["under_covered"]:
        print(f"     - {lemma}（{c} 次）")
    for lemma in coverage["missing"]:
        print(f"     - {lemma}（0 次）")

    problem_list = "\n".join(f"- {p}" for p in problems)
    user_msg = (
        f"The story below is missing some target words. Please rewrite it to include each "
        f"of these words at least once (any natural form is fine):\n{problem_list}\n\n"
        f"Current story:\n" + "\n".join(f"{s['id']}. {s['en']}" for s in story["sentences"]) +
        "\n\nReturn the COMPLETE updated story JSON. Return ONLY the JSON object, no prose, no fences."
    )
    return chat_json(messages=[("system", system), ("user", user_msg)], temperature=0.5, timeout=600)


def file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def resolve_target_sentences(word_count: int) -> int:
    """根据主题词数算出目标句数。0.9 ratio, min 8, max 18。"""
    return max(8, min(18, round(word_count * 0.9)))


def generate_one(
    *,
    vocab: dict,
    theme: dict,
    out_path: Path,
    force: bool,
    max_pass2: int,
    no_pass2: bool,
    is_review: bool = False,
):
    """生成一个故事（主题模式或复习模式）。"""
    theme_id = theme["id"]
    theme_name_zh = theme.get("name_zh", "")
    theme_name_en = theme.get("name_en", "")
    scene_description = theme.get("scene_description", "")
    character_focus = theme.get("character_focus", [])

    # 该主题的词
    word_lemmas = set(theme["word_list"])
    words_subset = [w for w in vocab["words"] if w["lemma"] in word_lemmas]
    target_sentences = resolve_target_sentences(len(words_subset))

    # 检查是否要跳过
    if out_path.exists() and not force:
        print(f"⏭️  已有 {out_path.name}（用 --force 重跑）")
        return

    system, user_tmpl = load_prompts()
    user_prompt = render_user_prompt(
        user_tmpl,
        theme_name_zh=theme_name_zh,
        theme_name_en=theme_name_en,
        scene_description=scene_description,
        character_focus=character_focus,
        words=words_subset,
        target_sentences=target_sentences,
    )

    label = "Review" if is_review else f"主题 [{theme_id}]"
    print(f"\n{'='*60}")
    print(f"📖 {label}: {theme_name_zh} / {theme_name_en}")
    print(f"   词数：{len(words_subset)}  目标句数：{target_sentences}")
    print(f"💬 调用 mmx text chat（M2.7）...")

    # Pass 1
    story = chat_json(
        messages=[("system", system), ("user", user_prompt)],
        max_tokens=4000,
        timeout=600,
    )
    story, coverage = validate_story(story, words_subset, target_sentences)
    print(f"  Pass-1 覆盖：{format_report(coverage)}")

    # Pass-2
    pass2_count = 0
    while not coverage["all_met"] and pass2_count < max_pass2 and not no_pass2:
        pass2_count += 1
        story = regenerate_for_missing(story, words_subset, system, coverage)
        story, coverage = validate_story(story, words_subset, target_sentences)
        print(f"  Pass-2 第 {pass2_count} 轮：{format_report(coverage)}")

    # 写 story JSON
    story["_meta"] = {
        "theme_id": theme_id,
        "theme_name_zh": theme_name_zh,
        "theme_name_en": theme_name_en,
        "is_review": is_review,
        "vocab_sha256": file_hash(REPO_ROOT / "units" / vocab.get("_vocab_path", "")) if vocab.get("_vocab_path") else "",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "regeneration_count": pass2_count,
        "coverage": {
            "total": coverage["total"],
            "covered": coverage["covered"],
            "missing": coverage["missing"],
        },
    }
    write_json(out_path, story)

    status = "🎉" if coverage["all_met"] else "⚠️"
    print(f"   {status} {out_path.name}：{coverage['covered']}/{coverage['total']} 词覆盖")


def main():
    ap = argparse.ArgumentParser(description="AI 故事生成（主题模式）")
    ap.add_argument("unit_path", help="单元路径，如 waiyan/7a/Unit01")
    ap.add_argument("--theme", help="主题 id（从 planner.json）")
    ap.add_argument("--review", action="store_true", help="生成 review 主题的兜底故事")
    ap.add_argument("--all", action="store_true", help="生成所有主题 + review")
    ap.add_argument("--force", action="store_true", help="强制重跑")
    ap.add_argument("--max-pass2", type=int, default=2)
    ap.add_argument("--no-pass2", action="store_true", help="跳过 Pass-2")
    args = ap.parse_args()

    unit_path = REPO_ROOT / "units" / args.unit_path
    vocab_path = unit_path / "vocab.json"
    if not vocab_path.exists():
        print(f"❌ 词表不存在：{vocab_path}", file=sys.stderr)
        sys.exit(1)

    vocab = read_json(vocab_path)
    out_dir = REPO_ROOT / "generated" / args.unit_path
    out_dir.mkdir(parents=True, exist_ok=True)

    # 加载 planner
    planner_path = out_dir / "planner.json"
    if not planner_path.exists():
        print(f"❌ planner.json 不存在：{planner_path}", file=sys.stderr)
        print(f"   先运行: python scripts/plan_curriculum.py {args.unit_path}", file=sys.stderr)
        sys.exit(1)
    planner = read_json(planner_path)

    # 决定要跑哪些主题
    tasks = []  # [(theme_dict, out_path, is_review)]

    if args.all:
        for t in planner.get("themes", []):
            tasks.append((t, out_dir / f"story_{t['id']}.json", False))
        if planner.get("review", {}).get("word_list"):
            tasks.append((planner["review"], out_dir / "story_review.json", True))
    elif args.review:
        if not planner.get("review", {}).get("word_list"):
            print(f"❌ planner.json 中没有 review 主题", file=sys.stderr)
            sys.exit(1)
        tasks.append((planner["review"], out_dir / "story_review.json", True))
    elif args.theme:
        theme = next((t for t in planner.get("themes", []) if t["id"] == args.theme), None)
        if not theme:
            print(f"❌ 主题 '{args.theme}' 不在 planner.json 里", file=sys.stderr)
            print(f"   可用主题：{[t['id'] for t in planner.get('themes', [])]}", file=sys.stderr)
            sys.exit(1)
        tasks.append((theme, out_dir / f"story_{args.theme}.json", False))
    else:
        # 传统模式：所有词 → story.json
        legacy_theme = {
            "id": "legacy-all",
            "name_zh": vocab.get("unit_title_zh", "全部词"),
            "name_en": vocab.get("unit_title_en", "All Words"),
            "scene_description": vocab.get("topic_hint", ""),
            "character_focus": [],
            "word_list": [w["lemma"] for w in vocab["words"]],
        }
        tasks.append((legacy_theme, out_dir / "story.json", False))
        print(f"⚠️  传统模式：所有词生成一个 story.json（建议用 --all 跑多故事模式）")

    # 跑
    for theme, out_path, is_review in tasks:
        generate_one(
            vocab=vocab,
            theme=theme,
            out_path=out_path,
            force=args.force,
            max_pass2=args.max_pass2,
            no_pass2=args.no_pass2,
            is_review=is_review,
        )

    print(f"\n{'='*60}")
    print(f"✅ 完成。共 {len(tasks)} 个故事。")


if __name__ == "__main__":
    main()
