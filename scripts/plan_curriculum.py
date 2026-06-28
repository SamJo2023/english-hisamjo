#!/usr/bin/env python3
"""Curriculum Planner: 把单元词表按主题分组。

输入：units/<path>/vocab.json
输出：generated/<path>/planner.json

每个 theme 是一篇短故事的主题，包含 10-18 个词。
review 是剩余词的兜底短故事。

用法：
  python scripts/plan_curriculum.py waiyan/7a/Unit01 [--force]
"""
import argparse
import json
import sys
from pathlib import Path

# UTF-8 输出
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))
from lib.json_io import read_json, write_json  # noqa: E402
from lib.mmx_text import chat_json  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = REPO_ROOT / "prompts"


def load_planner_prompts() -> tuple[str, str]:
    system = (PROMPTS_DIR / "planner.system.md").read_text(encoding="utf-8")
    user_tmpl = (PROMPTS_DIR / "planner.user.md").read_text(encoding="utf-8")
    return system, user_tmpl


def render_user_prompt(user_tmpl: str, vocab: dict) -> str:
    word_lines = []
    for w in sorted(vocab["words"], key=lambda x: x["lemma"]):
        word_lines.append(f"- {w['lemma']} [{w['pos']}] — {w['gloss_zh']}")
    word_list = "\n".join(word_lines)

    return (user_tmpl
        .replace("{{textbook}}", vocab.get("textbook", ""))
        .replace("{{unit_number}}", str(vocab["unit"]))
        .replace("{{unit_title_en}}", vocab.get("unit_title_en", ""))
        .replace("{{unit_title_zh}}", vocab.get("unit_title_zh", ""))
        .replace("{{word_count}}", str(len(vocab["words"])))
        .replace("{{word_list}}", word_list)
    )


def validate_planner(planner: dict, vocab: dict) -> list[str]:
    """校验 planner 输出是否覆盖了所有词。返回错误列表（空=通过）。"""
    errors = []
    input_lemmas = set(w["lemma"] for w in vocab["words"])
    assigned = set()

    for theme in planner.get("themes", []):
        for lemma in theme.get("word_list", []):
            if lemma not in input_lemmas:
                errors.append(f"Theme '{theme.get('id')}': 词 '{lemma}' 不在 vocab 里")
            elif lemma in assigned:
                errors.append(f"词 '{lemma}' 在多个 theme 里重复")
            else:
                assigned.add(lemma)

    for lemma in planner.get("review", {}).get("word_list", []):
        if lemma not in input_lemmas:
            errors.append(f"Review: 词 '{lemma}' 不在 vocab 里")
        elif lemma in assigned:
            errors.append(f"词 '{lemma}' 在 review 里与 theme 重复")
        else:
            assigned.add(lemma)

    missing = input_lemmas - assigned
    if missing:
        errors.append(f"未分配的词：{', '.join(sorted(missing))}")

    extra = assigned - input_lemmas
    if extra:
        errors.append(f"额外分配的词（不在 vocab）：{', '.join(sorted(extra))}")

    return errors


def auto_fix_planner(planner: dict, vocab: dict) -> tuple[dict, list[str]]:
    """自动修复 LLM 输出的常见错误：
    1. 删除不在 vocab 里的幻觉词
    2. 删除跨主题/跨 review 的重复词（保留第一次出现）
    3. 把未分配的 vocab 词按主题关键词分配到最合适的主题
    4. 都分不出去的最后放进 review

    Returns:
        (fixed_planner, fix_notes)
    """
    input_lemmas = set(w["lemma"] for w in vocab["words"])
    notes = []
    seen: set[str] = set()  # 全局已分配词集合

    # Step 1: 删除幻觉词 + 跨主题去重
    for theme in planner.get("themes", []):
        original = list(theme.get("word_list", []))
        cleaned = []
        dropped_hallucination = set()
        dropped_duplicate = set()
        for w in original:
            if w not in input_lemmas:
                dropped_hallucination.add(w)
            elif w in seen:
                dropped_duplicate.add(w)
            else:
                cleaned.append(w)
                seen.add(w)
        if dropped_hallucination:
            notes.append(f"[{theme['id']}] 移除幻觉词: {dropped_hallucination}")
        if dropped_duplicate:
            notes.append(f"[{theme['id']}] 移除重复词: {dropped_duplicate}")
        theme["word_list"] = cleaned

    # Step 2: review 也去重
    review = planner.setdefault("review", {"id": "review", "name_en": "Misc", "name_zh": "杂项", "word_list": []})
    original = list(review.get("word_list", []))
    cleaned = []
    dropped_hallucination = set()
    dropped_duplicate = set()
    for w in original:
        if w not in input_lemmas:
            dropped_hallucination.add(w)
        elif w in seen:
            dropped_duplicate.add(w)
        else:
            cleaned.append(w)
            seen.add(w)
    if dropped_hallucination:
        notes.append(f"[review] 移除幻觉词: {dropped_hallucination}")
    if dropped_duplicate:
        notes.append(f"[review] 移除重复词: {dropped_duplicate}")
    review["word_list"] = cleaned

    # Step 3: 找未分配的词，按主题关键词分配
    unassigned = input_lemmas - seen

    theme_keywords = {
        "barber": ["barber", "wig", "scissors", "hat", "customer", "hair", "shop", "理发", "剪刀", "假发", "帽子"],
        "factory": ["chocolate", "factory", "magical", "town", "rich", "poor", "cabbage", "watery", "freezing", "sunless", "bath"],
        "detective": ["letter", "instruction", "post office", "office", "wave", "voice", "shame", "smart", "believ", "reason", "example", "experience", "presentation", "survey", "happen", "everything", "fall", "touch", "empty", "finally", "receive", "surprised", "himself", "herself", "princess", "crown", "becom"],
    }

    for lemma in sorted(unassigned):
        placed = False
        lemma_lower = lemma.lower()
        for theme in planner.get("themes", []):
            theme_id = theme.get("id", "").lower()
            for cat, keywords in theme_keywords.items():
                if cat in theme_id:
                    if any(kw.lower() in lemma_lower or lemma_lower in kw.lower() for kw in keywords):
                        theme["word_list"].append(lemma)
                        theme["word_list"].sort()
                        notes.append(f"未分配词 '{lemma}' 放入 [{theme['id']}]（关键词匹配）")
                        placed = True
                        break
            if placed:
                break
        if not placed:
            review["word_list"].append(lemma)
            review["word_list"].sort()
            notes.append(f"未分配词 '{lemma}' 放入 [review]（兜底）")

    return planner, notes


def main():
    ap = argparse.ArgumentParser(description="Curriculum Planner（vocab.json → planner.json）")
    ap.add_argument("unit_path", help="单元路径，如 waiyan/7a/Unit01")
    ap.add_argument("--force", action="store_true", help="忽略现有 planner.json 强制重跑")
    args = ap.parse_args()

    unit_path = REPO_ROOT / "units" / args.unit_path
    vocab_path = unit_path / "vocab.json"
    if not vocab_path.exists():
        print(f"❌ 词表不存在：{vocab_path}", file=sys.stderr)
        sys.exit(1)

    vocab = read_json(vocab_path)
    out_dir = REPO_ROOT / "generated" / args.unit_path
    out_dir.mkdir(parents=True, exist_ok=True)
    planner_path = out_dir / "planner.json"

    if planner_path.exists() and not args.force:
        print(f"⏭️  已有 planner.json（用 --force 重跑）")
        print(f"   {planner_path}")
        sys.exit(0)

    system, user_tmpl = load_planner_prompts()
    user_prompt = render_user_prompt(user_tmpl, vocab)

    print(f"📖 词表：{len(vocab['words'])} 个词")
    print(f"💬 调用 mmx text chat 做主题分组...")

    planner = chat_json(
        messages=[("system", system), ("user", user_prompt)],
        max_tokens=4000,
        temperature=0.5,
        timeout=300,
    )

    # 自动修复常见 LLM 错误
    planner, fix_notes = auto_fix_planner(planner, vocab)
    if fix_notes:
        print(f"🔧 自动修复：")
        for n in fix_notes:
            print(f"   - {n}")

    # 校验
    errors = validate_planner(planner, vocab)
    if errors:
        print(f"⚠️  Planner 校验仍未通过：")
        for e in errors:
            print(f"   - {e}")
        write_json(planner_path, planner)
        sys.exit(1)

    # 写 planner.json
    write_json(planner_path, planner)
    print(f"✅ 已写入 {planner_path.relative_to(REPO_ROOT)}")

    # 打印主题摘要
    n = len(planner.get("themes", []))
    r = len(planner.get("review", {}).get("word_list", []))
    total = sum(len(t["word_list"]) for t in planner.get("themes", [])) + r
    print(f"\n📚 主题分组：{n} 个主题 + 1 个 review，共 {total} 词")
    for t in planner.get("themes", []):
        print(f"  [{t['id']}] {t['name_zh']} / {t['name_en']}（{len(t['word_list'])} 词）")
    if r > 0:
        print(f"  [review] {planner['review']['name_zh']} / {planner['review']['name_en']}（{r} 词）")


if __name__ == "__main__":
    main()
