#!/usr/bin/env python3
"""run_unit.py — 一键新单元流水线

按顺序跑 7 步，每步 idempotent（输出存在则 skip，除非 --force）：

  1. import_vocab           （仅 --vocab 模式：md/csv → units/<...>/vocab.json）
  2. plan_curriculum        （vocab.json → planner.json，按主题分组）
  3. check_covers           （planner.json → 检查 data/covers/ 是否齐全；缺则 exit 1）
  4. generate_story         （4 个 story_*.json + story_*.html）
  5. generate_tts           （audio/<theme>/sent-*.mp3）
  6. generate_word_audio    （data/word_audio/<lemma>.mp3，点击查词弹窗用）
  7. render <unit>          （单元 index.html）
  8. render（无参）          （根 index.html）

用法：
  # 模式 A：词表文件 + 单元路径（首次添加新单元）
  python scripts/run_unit.py --vocab path/to/vocab.md waiyan/7a/Unit02

  # 模式 B：单元路径（vocab.json 已存在，改完词表后重跑）
  python scripts/run_unit.py waiyan/7a/Unit02

  # 强制重跑全部（不 skip 已存在产物）
  python scripts/run_unit.py waiyan/7a/Unit02 --force

  # 只跑到第 5 步（不重渲 HTML）
  python scripts/run_unit.py waiyan/7a/Unit02 --stop-after word_audio

  # 跑全部但不动根 index.html
  python scripts/run_unit.py waiyan/7a/Unit02 --skip-render-root
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPTS = REPO_ROOT / "scripts"

# Pipeline 步骤定义：(name, [script_path, ...args_builder(unit_path)])
# args_builder 接受 unit_path 和 force flag，返回参数列表
STEPS = [
    ("plan_curriculum",   lambda u, f: ["plan_curriculum.py", u] + (["--force"] if f else [])),
    ("check_covers",      lambda u, f: ["check_covers.py", u]),  # 检测是幂等的，无 --force 概念
    ("generate_story",    lambda u, f: ["generate_story.py", u, "--all"] + (["--force"] if f else [])),
    ("generate_tts",      lambda u, f: ["generate_tts.py", u] + (["--force"] if f else [])),
    ("generate_word_audio", lambda u, f: ["generate_word_audio.py", u] + (["--force"] if f else [])),
    ("render_unit",       lambda u, f: ["render.py", u] + (["--force"] if f else [])),
]

# Stop-after 关键字 → 步骤名（包含该步骤）。None = 跑完
STOP_AFTER = {
    "plan":       "plan_curriculum",
    "check_covers": "check_covers",
    "story":      "generate_story",
    "tts":        "generate_tts",
    "word_audio": "generate_word_audio",
    "render":     "render_unit",
    "all":        None,  # 跑完
}


def run_step(name: str, cmd: list[str]) -> bool:
    """跑一步。返回 True 成功，False 失败。"""
    bar = "=" * 64
    print(f"\n{bar}\n[STEP] {name}\n  $ python scripts/{' '.join(cmd)}\n{bar}", flush=True)
    # 强制子进程用 UTF-8 输出（Windows GBK 默认会让中文/特殊字符乱码）
    env = {**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / cmd[0])] + cmd[1:],
        cwd=REPO_ROOT,
        env=env,
    )
    if result.returncode != 0:
        print(f"\n[FAIL] '{name}' exit code {result.returncode}", file=sys.stderr)
        return False
    return True


def main():
    ap = argparse.ArgumentParser(
        description="一键新单元流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("unit_path", help="单元路径，如 waiyan/7a/Unit02")
    ap.add_argument("--vocab", help="词表文件（md/csv）。提供时先跑 import_vocab.py")
    ap.add_argument("--force", action="store_true", help="强制重跑所有步骤（不 skip）")
    ap.add_argument(
        "--stop-after",
        choices=list(STOP_AFTER.keys()),
        default="all",
        help="跑到哪一步就停。默认 all（跑完所有步骤）",
    )
    ap.add_argument("--skip-render-root", action="store_true", help="跳过根 index.html 重渲")
    args = ap.parse_args()

    # 预检查：单元路径合法性
    unit_path = args.unit_path
    if not unit_path:
        print("[FAIL] 必须提供 unit_path", file=sys.stderr)
        sys.exit(1)

    # Step 0（可选）：import_vocab
    if args.vocab:
        vocab_src = Path(args.vocab)
        if not vocab_src.exists():
            print(f"[FAIL] 词表文件不存在: {vocab_src}", file=sys.stderr)
            sys.exit(1)
        vocab_out = REPO_ROOT / "units" / unit_path / "vocab.json"
        vocab_out.parent.mkdir(parents=True, exist_ok=True)
        if not run_step("import_vocab", ["import_vocab.py", str(vocab_src), "--out", str(vocab_out)]):
            sys.exit(1)

    # 检查 vocab.json 必须存在（除非刚刚 import 过）
    vocab_json = REPO_ROOT / "units" / unit_path / "vocab.json"
    if not vocab_json.exists():
        print(f"[FAIL] vocab.json 不存在: {vocab_json}", file=sys.stderr)
        print(f"   提示：用 --vocab <词表文件> 自动导入，或先手动跑 import_vocab.py", file=sys.stderr)
        sys.exit(1)

    # 跑管线步骤
    stop_marker = STOP_AFTER[args.stop_after]
    for name, builder in STEPS:
        cmd = builder(unit_path, args.force)
        if not run_step(name, cmd):
            sys.exit(1)
        if stop_marker and name == stop_marker:
            break

    # 收尾：根 index.html
    if not args.skip_render_root and args.stop_after == "all":
        # 只有单元的 planner 完整时根 index.html 才有意义；render.py 本身就 idempotent
        if not run_step("render_root", ["render.py"]):
            sys.exit(1)

    print(f"\n{'=' * 64}")
    print(f"[OK] Unit pipeline complete: {unit_path}")
    print(f"   本地预览: python serve.py -> http://localhost:8765/{unit_path}/")
    print(f"{'=' * 64}")


if __name__ == "__main__":
    main()
