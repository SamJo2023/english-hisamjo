#!/usr/bin/env python3
"""词表导入工具：支持两种输入格式 → 输出标准 vocab.json。

支持格式：
1. .md 格式（你拍照 OCR 后整理的格式）：
   word /ˈfəʊnɪk/ n. 中文翻译 页码
   post office 邮政局 12   ← 短语无音标，自动识别

2. .csv 格式：
   word,phonetic,pos,gloss_zh
   elephant,/ˈelɪfənt/,n.,大象

用法：
  python scripts/import_vocab.py v/m01.md \\
      --out units/waiyan/7a/Unit01/vocab.json \\
      --unit-title-zh "Module 1 查理和巧克力工厂" \\
      --unit-title-en "Charlie and the Chocolate Factory" \\
      --topic-hint "查理参观 Wonka 工厂的奇幻冒险故事片段"

字段含义见 units/waiyan/7a/Unit01/vocab.json schema。
"""
import argparse
import csv
import re
import sys
from pathlib import Path

# 强制 UTF-8 输出，修复 Windows GBK 编码下 emoji 报错
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass  # Python < 3.7 / 已关闭

# 让 import 时能 import 同目录的 lib
sys.path.insert(0, str(Path(__file__).parent))
from lib.json_io import write_json  # noqa: E402


# .md 格式正则（允许省略音标和词性，处理短语如 "post office 邮政局 12"）
# 优先级：FULL（有 pos）→ PHRASE（无 pos）
_MD_LINE_FULL = re.compile(
    r"""^
    (?P<lemma>[A-Za-z][A-Za-z\s'-]+?)      # 词条（非贪婪，给后面的可选部分留位置）
    \s+(?P<phon>/[^/]+/)?                  # 可选音标
    \s*(?P<pos>(?:n|v|adj|adv|pron|prep|conj|art|num|int|phr|aux|vi|vt)\.?)?
    \s+(?P<gloss>[^0-9].*?)                 # 中文释义（不以数字开头；用 .*? 不是 .+?，让单字 gloss 不吃掉页码前的空格）
    \s+(?P<page>\d+)\s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)
_MD_LINE_PHRASE = re.compile(
    r"^(?P<lemma>[A-Za-z][A-Za-z\s'-]+)\s+(?P<gloss>[^0-9].*?)\s+(?P<page>\d+)\s*$"
)


def parse_md_line(line: str) -> dict | None:
    """解析一行 md 格式词条。失败返回 None。"""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    # 先尝试完整格式（含 pos）
    m = _MD_LINE_FULL.match(line)
    if m:
        lemma = m.group("lemma").strip()
        phon = (m.group("phon") or "").strip("/")
        pos = (m.group("pos") or "").strip()
        gloss = m.group("gloss").strip()
        page = int(m.group("page"))
    else:
        # 退化到短语格式（无音标无 pos，如 "post office 邮政局 12"）
        m = _MD_LINE_PHRASE.match(line)
        if not m:
            return None
        lemma = m.group("lemma").strip()
        phon = ""
        pos = "phr."  # 多词无 pos 默认短语
        gloss = m.group("gloss").strip()
        page = int(m.group("page"))
    # 标准化 pos
    if not pos.endswith("."):
        pos = pos + "."
    is_phrase = " " in lemma or "-" in lemma or pos == "phr."
    return {
        "lemma": lemma,
        "pos": pos,
        "gloss_zh": gloss,
        "phonetic_uk": phon,
        "phonetic_us": phon,
        "page": page,
        "is_phrase": is_phrase,
        "accept_forms": [],
    }


def parse_md(path: Path) -> list[dict]:
    """从 .md 文件解析词条列表。"""
    words = []
    errors = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        rec = parse_md_line(line)
        if rec is None:
            if line.strip() and not line.strip().startswith("#"):
                errors.append(f"  line {lineno}: 无法解析 → {line.strip()}")
        else:
            words.append(rec)
    if errors:
        print("⚠️  以下行未解析（请检查格式）：", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
    return words


def parse_csv(path: Path) -> list[dict]:
    """从 .csv 文件解析词条列表。期望列：word, phonetic, pos, gloss_zh。"""
    words = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemma = (row.get("word") or row.get("lemma") or "").strip()
            if not lemma:
                continue
            phon = (row.get("phonetic") or "").strip().strip("/")
            pos = (row.get("pos") or "n.").strip()
            if not pos.endswith("."):
                pos = pos + "."
            gloss = (row.get("gloss_zh") or row.get("gloss") or "").strip()
            is_phrase = " " in lemma or "-" in lemma
            words.append({
                "lemma": lemma,
                "pos": pos,
                "gloss_zh": gloss,
                "phonetic_uk": phon,
                "phonetic_us": phon,
                "is_phrase": is_phrase,
                "accept_forms": [],
            })
    return words


def main():
    ap = argparse.ArgumentParser(description="词表导入工具（md / csv → vocab.json）")
    ap.add_argument("input", help="输入文件（.md 或 .csv）")
    ap.add_argument("--out", required=True, help="输出 vocab.json 路径")
    ap.add_argument("--textbook", default="waiyan", help="教材标识（默认 waiyan = 外研版）")
    ap.add_argument("--grade", default="7a", help="年级（默认 7a = 初一上）")
    ap.add_argument("--unit", type=int, required=True, help="单元号（整数，如 1）")
    ap.add_argument("--unit-title-zh", default="", help="单元中文标题")
    ap.add_argument("--unit-title-en", default="", help="单元英文标题")
    ap.add_argument("--topic-hint", default="", help="故事主题提示（给 LLM）")
    ap.add_argument("--target-sentences", type=int, default=None,
                    help="目标句子数（默认按词数自动：max(15, round(词数*1.0))）")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"❌ 输入文件不存在：{src}", file=sys.stderr)
        sys.exit(1)

    if src.suffix.lower() == ".md":
        words = parse_md(src)
    elif src.suffix.lower() == ".csv":
        words = parse_csv(src)
    else:
        print(f"❌ 不支持的文件格式：{src.suffix}（仅支持 .md / .csv）", file=sys.stderr)
        sys.exit(1)

    if not words:
        print("❌ 没有解析出任何词条。", file=sys.stderr)
        sys.exit(1)

    # 自动算 target_sentences
    n = len(words)
    target = args.target_sentences if args.target_sentences is not None else max(15, round(n * 1.0))

    vocab = {
        "schema_version": 1,
        "textbook": args.textbook,
        "grade": args.grade,
        "unit": args.unit,
        "unit_title_zh": args.unit_title_zh,
        "unit_title_en": args.unit_title_en,
        "topic_hint": args.topic_hint,
        "config": {
            "target_sentences": target,
            "min_occurrences_per_word": 2,
            "tts_voice": "tianxin_xiaoling",
            "tts_speed": 1.0,
        },
        "words": words,
    }

    out = Path(args.out)
    write_json(out, vocab)
    print(f"✅ 已写入 {out}")
    print(f"   词条数：{n}")
    print(f"   短语数：{sum(1 for w in words if w['is_phrase'])}")
    print(f"   target_sentences：{target}（按词数自动）")
    if not args.topic_hint:
        print(f"   ⚠️  未提供 --topic-hint，建议在 JSON 里补上（影响 LLM 故事质量）")
    if not args.unit_title_zh:
        print(f"   ⚠️  未提供 --unit-title-zh")


if __name__ == "__main__":
    main()
