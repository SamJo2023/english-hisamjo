"""一次性脚本：不重跑 LLM，只重跑 coverage 校验。"""
import sys
import json
from pathlib import Path

# Force UTF-8
for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.coverage import check_coverage, format_report

REPO_ROOT = Path(__file__).resolve().parent.parent
UNIT = "waiyan/7a/Unit01"
vocab = json.loads((REPO_ROOT / "units" / UNIT / "vocab.json").read_text(encoding="utf-8"))
story = json.loads((REPO_ROOT / "generated" / UNIT / "story.json").read_text(encoding="utf-8"))

cov = check_coverage(
    vocab["words"],
    [s["en"] for s in story["sentences"]],
    min_occurrences=vocab["config"]["min_occurrences_per_word"],
)
print("=== 新覆盖报告（自动算曲折形式后）===")
print(format_report(cov))
print()
print("=== 每个词的命中数 ===")
for w in vocab["words"]:
    lemma = w["lemma"]
    cnt = cov["counts"][lemma]
    flag = "OK " if cnt >= 2 else ("1x " if cnt >= 1 else "MISS")
    print(f"  [{flag}] {lemma:<14} {cnt} 次")
