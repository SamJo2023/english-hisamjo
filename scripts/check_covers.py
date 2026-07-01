#!/usr/bin/env python3
"""检查单元的 planner.json 中所有 cover_id 是否在 data/covers/ 存在。

用法：
  python scripts/check_covers.py waiyan/7b/Unit04

退出码：0 全部存在；1 有缺失。

设计：只检测不修复（避免职责膨胀）。缺 cover 时打印每个缺失项 + mmx image
generate 命令模板，用户手动补完后用 --force 重跑 render_unit。
"""
import argparse
import sys
from pathlib import Path

# 强制 UTF-8 输出，修复 Windows GBK 编码下 emoji 报错
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# 让 import 时能 import 同目录的 lib
sys.path.insert(0, str(Path(__file__).parent))
from lib.json_io import read_json  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def check(unit_path: str) -> int:
    planner_path = REPO_ROOT / "generated" / unit_path / "planner.json"
    if not planner_path.exists():
        print(f"[FAIL] planner.json 不存在: {planner_path}", file=sys.stderr)
        print(f"   先跑: python scripts/plan_curriculum.py {unit_path}", file=sys.stderr)
        return 1

    planner = read_json(planner_path)
    targets = list(planner.get("themes", []))
    if planner.get("review"):
        targets.append(planner["review"])

    missing = []
    for t in targets:
        cover_id = t.get("cover_id") or t.get("id", "")
        cover_path = REPO_ROOT / "data" / "covers" / f"{cover_id}.png"
        if not cover_path.exists():
            missing.append((t.get("id"), cover_id, t.get("name_zh", ""), t.get("name_en", "")))

    if not missing:
        print(f"✅ {len(targets)} 个 cover 全部存在: {unit_path}")
        return 0

    print(f"[FAIL] {len(missing)}/{len(targets)} 个 cover 缺失: {unit_path}", file=sys.stderr)
    for tid, cid, name_zh, name_en in missing:
        print(f"   ❌ [{tid}] cover_id={cid} ({name_zh} / {name_en})", file=sys.stderr)
        print(f"      缺失: data/covers/{cid}.png", file=sys.stderr)

    print(f"\n💡 修复方法（参考 generate_covers.py 的 Identity V prompt 风格）：", file=sys.stderr)
    print(f"   # 1) 用 mmx image generate 补 cover（每张 30-60s）", file=sys.stderr)
    for tid, cid, name_zh, name_en in missing:
        print(f'   mmx image generate --model image-01 --aspect-ratio 16:9 \\', file=sys.stderr)
        print(f'     --out data/covers/{cid}.png \\', file=sys.stderr)
        print(f'     --prompt "Identity V 风格 16:9 插图，<{name_en} 场景描述>"', file=sys.stderr)
    print(f"\n   # 2) 补完后强制重渲 Unit（仅 story HTML）：", file=sys.stderr)
    print(f"   python scripts/render.py {unit_path} --force", file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser(description="检查单元 cover 图是否存在")
    ap.add_argument("unit_path", help="单元路径，如 waiyan/7b/Unit04")
    args = ap.parse_args()
    sys.exit(check(args.unit_path))


if __name__ == "__main__":
    main()