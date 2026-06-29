#!/usr/bin/env python3
"""一次性预处理器：v/Unit2.md → units/waiyan/7a/Unit02/vocab-source.md

两步走：
1. join_split_lines：把跨行拆开的词条合并成一行（用页码作为词条边界）
2. find_entry：对合并后的每行找词条（多词走 PHRASE，单词走 WORD）
3. 处理行内混搭（"任何一个 choice ..."）和续行去重
"""
import re
from pathlib import Path
import sys

SRC = Path("v/Unit2.md")
DST = Path("units/waiyan/7a/Unit02/vocab-source.md")

# 匹配行尾页码
PAGE_END = re.compile(r"\s+\d+\s*$")

POS_SET = {"n", "v", "adj", "adv", "pron", "prep", "conj", "art", "num", "int", "phr", "aux", "vi", "vt"}

# 单词行：lemma + (可选 /phon/) + (可选 pos) + gloss + page
# 关键：gloss 用 [^0-9].*? （0+ 字符），不要用 [^0-9].+? （1+ 字符，会吃掉 page 前的空格）
WORD_PAT = re.compile(
    r"(?P<lemma>[A-Za-z][A-Za-z'\-]+)"
    r"(?:\s*/(?P<phon>[^/\s]+)/)?"
    r"(?:\s+(?P<pos>(?:n|v|adj|adv|pron|prep|conj|art|num|int|phr|aux|vi|vt)\.?))?"
    r"\s+(?P<gloss>[^0-9].*?)"
    r"\s+(?P<page>\d+)\s*$",
    re.IGNORECASE,
)

# 短语行：2+ 个英文词（无音标无词性）+ gloss + page
PHRASE_PAT = re.compile(
    r"(?P<lemma>(?:[A-Za-z][A-Za-z'\-]*\s+){1,}[A-Za-z][A-Za-z'\-]*)"
    r"\s+(?P<gloss>[^0-9].*?)"
    r"\s+(?P<page>\d+)\s*$"
)


def fix_pos(pos: str | None) -> str:
    if not pos:
        return ""
    pos = pos.strip()
    return pos if pos.endswith(".") else pos + "."


def join_split_lines(raw_lines: list[str]) -> list[str]:
    """把被换行拆开的词条合并成一行。

    规则：从上往下扫，凡是"行尾不是页码"的行，跟后续行用空格拼起来，
    直到遇到一个"行尾是页码"的行，作为这一段的结束（buffer + 当前行拼一起 emit）。
    """
    result = []
    buffer: list[str] = []
    for raw in raw_lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            if buffer:
                result.append(" ".join(buffer))
                buffer = []
            result.append(raw)
            continue
        if PAGE_END.search(line):
            # buffer 中所有无页码行 + 这行带页码行 → 直接拼接（不补空格）
            if buffer:
                result.append("".join(buffer + [line]))
                buffer = []
            else:
                result.append(line)
        else:
            buffer.append(line)
    if buffer:
        result.append("".join(buffer))
    return result


def find_entry(line: str):
    """返回 (start_idx, entry_dict) 或 None。

    策略：先 PHRASE_PAT（多词短语），后 WORD_PAT（单词）。
    """
    # PHRASE 优先
    pm = list(PHRASE_PAT.finditer(line))
    if pm:
        m = pm[-1]
        lemma = m.group("lemma").strip()
        if " " in lemma:
            return m.start(), {
                "lemma": lemma, "phon": "", "pos": "phr.",
                "gloss": m.group("gloss").strip(),
                "page": int(m.group("page")),
                "kind": "phrase",
            }
    # WORD（单词）
    wm = list(WORD_PAT.finditer(line))
    if wm:
        m = wm[-1]
        lemma = m.group("lemma").strip()
        if " " not in lemma:
            return m.start(), {
                "lemma": lemma,
                "phon": (m.group("phon") or "").strip(),
                "pos": fix_pos(m.group("pos")),
                "gloss": m.group("gloss").strip(),
                "page": int(m.group("page")),
                "kind": "word",
            }
    return None


def merge_continuation(gloss: str, cont: str) -> str:
    """接续行：去末尾页码，去重，加到 gloss。"""
    cont = cont.strip()
    cont = re.sub(r"\s+\d+\s*$", "", cont).strip()
    if not cont:
        return gloss
    if gloss.endswith(cont):
        return gloss
    return gloss + cont


def render_entry(entry: dict) -> str:
    lemma = entry["lemma"]
    phon = entry.get("phon", "")
    pos = entry.get("pos", "")
    gloss = entry["gloss"]
    page = entry["page"]
    if entry["kind"] == "phrase" or (not phon and not pos):
        return f"{lemma} {gloss} {page}"
    phon_str = f"/{phon}/" if phon else ""
    return f"{lemma} {phon_str} {pos} {gloss} {page}".strip()


def main():
    raw_lines = SRC.read_text(encoding="utf-8").splitlines()
    joined = join_split_lines(raw_lines)

    entries = []
    current = None

    def flush():
        nonlocal current
        if current:
            entries.append(current)
            current = None

    for lineno, raw in enumerate(joined, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        found = find_entry(line)
        if found:
            start_idx, entry = found
            prefix = line[:start_idx].strip()
            if prefix:
                if current:
                    current["gloss"] = merge_continuation(current["gloss"], prefix)
                else:
                    print(f"⚠️  line {lineno}: 续行但没有前一条 → {line[:80]}", file=sys.stderr)
            flush()
            current = entry
        else:
            if current:
                current["gloss"] = merge_continuation(current["gloss"], line)
            else:
                print(f"⚠️  line {lineno}: 孤立续行 → {line}", file=sys.stderr)

    flush()

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text("\n".join(render_entry(e) for e in entries) + "\n", encoding="utf-8")

    n_words = sum(1 for e in entries if e["kind"] == "word")
    n_phrases = sum(1 for e in entries if e["kind"] == "phrase")
    print(f"[OK] 已写入 {DST}")
    print(f"     词条总数: {len(entries)}（单词 {n_words} + 短语 {n_phrases}）")
    print()
    print("--- 全部词条 ---")
    for e in entries:
        print(f"  {render_entry(e)}")


if __name__ == "__main__":
    main()