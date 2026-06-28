"""词覆盖校验：检查 LLM 生成的故事中，每个目标词是否出现足够多次。

规则：
- 自动从 lemma + 词性生成常见曲折形式（believe → believed, believes, believing）
- 不规则动词/名词查内置表（go → went, gone; fall → fell, fallen）
- 单个词（is_phrase=False）：用词边界正则匹配（防止 'cat' 误匹配 'category'）
- 短语（is_phrase=True）：用子串匹配
- 大小写不敏感
- 同一位置的多次匹配只算一次（用位置去重）
"""
import re


# 不规则动词 / 名词表（精选，覆盖初一常见词）
_IRREGULAR = {
    "go": ["goes", "going", "went", "gone"],
    "be": ["am", "is", "are", "was", "were", "been", "being"],
    "have": ["has", "had", "having"],
    "do": ["does", "did", "doing", "done"],
    "say": ["says", "said", "saying"],
    "get": ["gets", "got", "gotten", "getting"],
    "make": ["makes", "made", "making"],
    "come": ["comes", "came", "coming"],
    "take": ["takes", "took", "taken", "taking"],
    "see": ["sees", "saw", "seen", "seeing"],
    "know": ["knows", "knew", "known", "knowing"],
    "give": ["gives", "gave", "given", "giving"],
    "find": ["finds", "found", "finding"],
    "think": ["thinks", "thought", "thinking"],
    "tell": ["tells", "told", "telling"],
    "become": ["becomes", "became", "becoming"],
    "show": ["shows", "showed", "shown", "showing"],
    "leave": ["leaves", "left", "leaving"],
    "feel": ["feels", "felt", "feeling"],
    "bring": ["brings", "brought", "bringing"],
    "begin": ["begins", "began", "begun", "beginning"],
    "keep": ["keeps", "kept", "keeping"],
    "hold": ["holds", "held", "holding"],
    "write": ["writes", "wrote", "written", "writing"],
    "stand": ["stands", "stood", "standing"],
    "hear": ["hears", "heard", "hearing"],
    "let": ["lets", "letting"],
    "mean": ["means", "meant", "meaning"],
    "meet": ["meets", "met", "meeting"],
    "pay": ["pays", "paid", "paying"],
    "sit": ["sits", "sat", "sitting"],
    "speak": ["speaks", "spoke", "spoken", "speaking"],
    "lead": ["leads", "led", "leading"],
    "read": ["reads", "reading"],
    "grow": ["grows", "grew", "grown", "growing"],
    "lose": ["loses", "lost", "losing"],
    "fall": ["falls", "fell", "fallen", "falling"],
    "send": ["sends", "sent", "sending"],
    "build": ["builds", "built", "building"],
    "understand": ["understands", "understood", "understanding"],
    "draw": ["draws", "drew", "drawn", "drawing"],
    "break": ["breaks", "broke", "broken", "breaking"],
    "spend": ["spends", "spent", "spending"],
    "rise": ["rises", "rose", "risen", "rising"],
    "drive": ["drives", "drove", "driven", "driving"],
    "buy": ["buys", "bought", "buying"],
    "wear": ["wears", "wore", "worn", "wearing"],
    "choose": ["chooses", "chose", "chosen", "choosing"],
    "blow": ["blows", "blew", "blown", "blowing"],
    "catch": ["catches", "caught", "catching"],
    "teach": ["teaches", "taught", "teaching"],
    "run": ["runs", "ran", "running"],
    "win": ["wins", "won", "winning"],
    "swim": ["swims", "swam", "swum", "swimming"],
    "ring": ["rings", "rang", "rung", "ringing"],
    "sing": ["sings", "sang", "sung", "singing"],
    "drink": ["drinks", "drank", "drunk", "drinking"],
    "forget": ["forgets", "forgot", "forgotten", "forgetting"],
    "wake": ["wakes", "woke", "woken", "waking"],
    "lie": ["lies", "lay", "lain", "lying"],
    "lay": ["lays", "laid", "laying"],
    "hang": ["hangs", "hung", "hanging"],
    "feed": ["feeds", "fed", "feeding"],
    "sell": ["sells", "sold", "selling"],
    "fight": ["fights", "fought", "fighting"],
    "shake": ["shakes", "shook", "shaken", "shaking"],
    "happen": ["happens", "happened", "happening"],
    "happen": ["happens", "happened", "happening"],
    "touch": ["touches", "touched", "touching"],
    "wave": ["waves", "waved", "waving"],
    "wave": ["waves", "waved", "waving"],
    "voice": ["voices", "voiced", "voicing"],
    "fall": ["falls", "fell", "fallen", "falling"],
    "shame": ["shames", "shamed", "shaming"],
    "blow": ["blows", "blew", "blown", "blowing"],
    "receive": ["receives", "received", "receiving"],
    "believe": ["believes", "believed", "believing"],
    "experience": ["experiences", "experienced", "experiencing"],
    "instruction": ["instructions", "instructed", "instructing"],
    "survey": ["surveys", "surveyed", "surveying"],
    "presentation": ["presentations"],
    "customer": ["customers"],
    "customer": ["customers"],
    "exciting": ["excited", "excite", "excites"],
    "magical": ["magic", "magically"],
    "freezing": ["freeze", "freezes", "froze", "frozen"],
    "sunless": ["sun"],
    "empty": ["emptied", "empties", "emptying"],
    "smart": ["smarter", "smartest"],
    "surprised": ["surprise", "surprises", "surprising"],
}


def normalize(text: str) -> str:
    """小写化 + 保留字母、空格、撇号、连字符。"""
    return re.sub(r"[^A-Za-z\s'-]", " ", text.lower())


def generate_inflections(lemma: str, pos: str) -> list[str]:
    """基于 lemma 和 pos 生成常见曲折形式。"""
    forms = [lemma]
    l = lemma.lower().strip()
    p = pos.lower().strip().rstrip(".")
    is_verb = p in ("v", "vi", "vt") or p.startswith("v ")
    is_noun = p in ("n",) or p.startswith("n ")
    is_adj = p in ("adj", "adj.", "a") or p.startswith("adj")
    is_adv = p in ("adv",)

    if is_verb:
        forms.extend([l + "s", l + "ed", l + "ing"])
        if l.endswith("e"):
            forms.append(l[:-1] + "ing")
            forms.append(l + "d")
        if len(l) > 1 and l.endswith("y") and l[-2] not in "aeiou":
            forms.append(l[:-1] + "ies")
            forms.append(l[:-1] + "ied")
        if len(l) >= 3 and l[-1] not in "aeiouwxy" and l[-2] in "aeiou" and l[-3] not in "aeiou":
            forms.append(l + l[-1] + "ing")
        if l in _IRREGULAR:
            forms.extend(_IRREGULAR[l])

    elif is_noun:
        forms.append(l + "s")
        if len(l) > 1 and l.endswith("y") and l[-2] not in "aeiou":
            forms.append(l[:-1] + "ies")
        if l.endswith(("s", "x", "ch", "sh")):
            forms.append(l + "es")
        if l.endswith("f"):
            forms.append(l[:-1] + "ves")
        if l.endswith("fe"):
            forms.append(l[:-2] + "ves")
        if l in _IRREGULAR:
            forms.extend(_IRREGULAR[l])

    elif is_adj:
        forms.extend([l + "er", l + "est"])
        if l.endswith("e"):
            forms.append(l + "r")
            forms.append(l + "st")
        if len(l) > 1 and l.endswith("y") and l[-2] not in "aeiou":
            forms.append(l[:-1] + "ier")
            forms.append(l[:-1] + "iest")
        if l in _IRREGULAR:
            forms.extend(_IRREGULAR[l])

    return list(set(f.lower() for f in forms if f))


def check_coverage(
    words: list[dict],
    sentences_en: list[str],
    *,
    min_occurrences: int = 2,
) -> dict:
    """检查故事中每个目标词的覆盖情况。"""
    full_text = " ".join(sentences_en)
    normalized = normalize(full_text)

    counts = {}
    meets_min = {}
    for w in words:
        lemma = w["lemma"]
        is_phrase = w.get("is_phrase", False) or " " in lemma or "-" in lemma

        if is_phrase:
            forms = [lemma] + (w.get("accept_forms") or [])
        else:
            pos = w.get("pos", "n.")
            forms = generate_inflections(lemma, pos) + (w.get("accept_forms") or [])

        positions = set()
        for form in forms:
            f = form.lower().strip()
            if not f:
                continue
            if is_phrase or " " in f or "-" in f:
                start = 0
                while True:
                    idx = normalized.find(f, start)
                    if idx == -1:
                        break
                    positions.add(idx)
                    start = idx + len(f)
            else:
                pattern = r"\b" + re.escape(f) + r"\b"
                for m in re.finditer(pattern, normalized):
                    positions.add(m.start())
        cnt = len(positions)
        counts[lemma] = cnt
        meets_min[lemma] = cnt >= min_occurrences

    missing = [lemma for lemma, c in counts.items() if c == 0]
    under_covered = [(lemma, c) for lemma, c in counts.items() if 0 < c < min_occurrences]
    covered = sum(1 for m in meets_min.values() if m)

    return {
        "total": len(words),
        "covered": covered,
        "missing": missing,
        "under_covered": under_covered,
        "all_met": covered == len(words),
        "counts": counts,
        "meets_min": meets_min,
    }


def format_report(coverage: dict) -> str:
    """人类可读的覆盖报告。"""
    lines = [f"覆盖：{coverage['covered']}/{coverage['total']}"]
    if coverage["missing"]:
        lines.append(f"  缺失({len(coverage['missing'])}): {', '.join(coverage['missing'])}")
    if coverage["under_covered"]:
        items = ", ".join(f"{l}({c})" for l, c in coverage["under_covered"])
        lines.append(f"  不足({len(coverage['under_covered'])}): {items}")
    if coverage["all_met"]:
        lines.append("  全部达标")
    return "\n".join(lines)
