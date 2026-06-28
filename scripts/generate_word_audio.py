#!/usr/bin/env python3
"""为 vocab.json 中的每个词生成发音 mp3。

输出：data/word_audio/<safe_lemma>.mp3
- lemma_safe：词表 lemma 替换空格/斜杠/撇号为 _
- 词性提示：可加 "factory, n." 让 TTS 更稳

用法：
  python scripts/generate_word_audio.py waiyan/7a/Unit01 [--force]
"""
import argparse
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))
from lib.json_io import read_json  # noqa: E402
from lib.mmx_speech import synthesize  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent


def safe_lemma(lemma: str) -> str:
    """lemma → 文件名安全字符串。"""
    s = lemma.replace("/", "_").replace(" ", "_").replace("'", "").replace("’", "")
    return s


def main():
    ap = argparse.ArgumentParser(description="为词表生成发音 mp3")
    ap.add_argument("unit_path", help="单元路径，如 waiyan/7a/Unit01")
    ap.add_argument("--voice", default="tianxin_xiaoling", help="TTS 音色")
    ap.add_argument("--speed", type=float, default=0.9, help="语速（0.7-1.0，默认 0.9 慢一点更清晰）")
    ap.add_argument("--force", action="store_true", help="强制重生成")
    args = ap.parse_args()

    vocab = read_json(REPO_ROOT / "units" / args.unit_path / "vocab.json")
    out_dir = REPO_ROOT / "data" / "word_audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    n = len(vocab["words"])
    print(f"📖 词表：{n} 个词")
    print(f"🎙  音色：{args.voice}  语速：{args.speed}x")
    print(f"📁 输出：{out_dir.relative_to(REPO_ROOT)}/")
    print()

    generated = 0
    skipped = 0
    failed = 0
    for w in vocab["words"]:
        lemma = w["lemma"]
        safe = safe_lemma(lemma)
        out = out_dir / f"{safe}.mp3"
        if out.exists() and not args.force:
            skipped += 1
            print(f"⏭️  {safe}.mp3 已存在")
            continue
        try:
            # 短停顿让发音清晰（mmx 会自动处理标点）
            synthesize(text=lemma, out_path=out, voice=args.voice, speed=args.speed)
            generated += 1
            print(f"✓ {safe}.mp3 ({lemma})")
        except Exception as e:
            failed += 1
            print(f"✗ {safe}.mp3 FAILED: {str(e)[:80]}")

    print()
    print(f"📊 完成：新生成 {generated} / 跳过 {skipped} / 失败 {failed}")


if __name__ == "__main__":
    main()
