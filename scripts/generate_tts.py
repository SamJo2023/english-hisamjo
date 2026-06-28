#!/usr/bin/env python3
"""为单元的所有故事生成 TTS 音频。

读 generated/<unit>/story_*.json → 为每个 story 生成：
- audio/<theme>/whole.mp3 （整段故事）
- audio/<theme>/sent-XX.mp3 （每句 1 个 mp3）

idempotent：跳过已生成且 story 未变的 mp3。

用法：
  python scripts/generate_tts.py waiyan/7a/Unit01
  python scripts/generate_tts.py waiyan/7a/Unit01 --voice tianxin_xiaoling --speed 0.9
  python scripts/generate_tts.py waiyan/7a/Unit01 --force
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

# UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))
from lib.json_io import read_json, write_json  # noqa: E402
from lib.mmx_speech import synthesize  # noqa: E402
from lib.normalize import normalize_text  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent


def file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def generate_story_audio(story_path: Path, voice: str, speed: float, force: bool) -> dict:
    """为单个 story_*.json 生成 TTS。"""
    story = read_json(story_path)
    theme_id = story["_meta"]["theme_id"]
    audio_dir = story_path.parent / "audio" / theme_id
    audio_dir.mkdir(parents=True, exist_ok=True)

    sentences = story["sentences"]
    n = len(sentences)
    print(f"\n{'='*60}")
    print(f"🎙  [{theme_id}] {n} 句 | {story.get('title_zh', '')}")

    # 文本预处理（智能引号 → ASCII、合并空白）
    for sent in sentences:
        sent["en_normalized"] = normalize_text(sent["en"])

    # hash 检查
    story_hash = file_hash(story_path)
    audio_meta_path = audio_dir / "_audio_meta.json"
    if audio_meta_path.exists() and not force:
        existing = read_json(audio_meta_path)
        if (existing.get("story_sha256") == story_hash
                and existing.get("voice") == voice
                and existing.get("speed") == speed):
            print(f"  ⏭️  跳过（story/voice/speed 未变）")
            return {"theme_id": theme_id, "skipped": True, "total": n}

    generated = []
    failed = []
    t_start = time.time()

    # 1) per-sentence
    for i, sent in enumerate(sentences, 1):
        out = audio_dir / f"sent-{i:02d}.mp3"
        if out.exists() and not force:
            generated.append({"id": sent["id"], "path": str(out), "status": "skipped"})
            continue
        try:
            synthesize(
                text=sent["en_normalized"],
                out_path=out,
                voice=voice,
                speed=speed,
            )
            generated.append({"id": sent["id"], "path": str(out), "status": "new"})
            elapsed = time.time() - t_start
            print(f"  ✓ {sent['id']} ({len(sent['en_normalized'])} 字符) [{elapsed:.1f}s]")
        except Exception as e:
            failed.append({"sentence_id": sent["id"], "error": str(e)[:200]})
            print(f"  ✗ {sent['id']} FAILED: {str(e)[:100]}")

    # 2) whole-story
    whole_out = audio_dir / "whole.mp3"
    if (not whole_out.exists()) or force:
        full_text = " ".join(s["en_normalized"] for s in sentences)
        try:
            synthesize(text=full_text, out_path=whole_out, voice=voice, speed=speed)
            elapsed = time.time() - t_start
            print(f"  ✓ whole.mp3 ({len(full_text)} 字符) [{elapsed:.1f}s]")
        except Exception as e:
            failed.append({"sentence_id": "whole", "error": str(e)[:200]})
            print(f"  ✗ whole.mp3 FAILED: {str(e)[:100]}")
    else:
        print(f"  ⏭️  whole.mp3 已存在")

    # 写 _audio_meta.json
    write_json(audio_meta_path, {
        "schema_version": 1,
        "theme_id": theme_id,
        "story_sha256": story_hash,
        "voice": voice,
        "speed": speed,
        "total_sentences": n,
        "generated_count": sum(1 for g in generated if g["status"] == "new"),
        "skipped_count": sum(1 for g in generated if g["status"] == "skipped"),
        "failed_count": len(failed),
        "failed_sentences": failed,
    })

    elapsed = time.time() - t_start
    new_n = sum(1 for g in generated if g["status"] == "new")
    print(f"  📊  {new_n} 新生成 / {n - new_n - len(failed)} 跳过 / {len(failed)} 失败 / 用时 {elapsed:.1f}s")

    return {
        "theme_id": theme_id,
        "skipped": False,
        "total": n,
        "new": new_n,
        "failed": len(failed),
    }


def main():
    ap = argparse.ArgumentParser(description="为单元的所有故事生成 TTS 音频")
    ap.add_argument("unit_path", help="单元路径，如 waiyan/7a/Unit01")
    ap.add_argument("--voice", default="tianxin_xiaoling", help="TTS 音色")
    ap.add_argument("--speed", type=float, default=1.0, help="语速（0.5-2.0）")
    ap.add_argument("--force", action="store_true", help="强制重生成")
    args = ap.parse_args()

    out_dir = REPO_ROOT / "generated" / args.unit_path
    if not out_dir.exists():
        print(f"❌ 单元目录不存在：{out_dir}", file=sys.stderr)
        sys.exit(1)

    # 找所有 story_*.json
    story_files = sorted(out_dir.glob("story_*.json"))
    if not story_files:
        print(f"❌ 没有找到 story_*.json 文件：{out_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"📖 单元：{args.unit_path}")
    print(f"🎙  音色：{args.voice}  语速：{args.speed}x")
    print(f"📁 输出：{out_dir}/audio/")

    total_sents = 0
    total_new = 0
    total_failed = 0
    for story_path in story_files:
        result = generate_story_audio(story_path, args.voice, args.speed, args.force)
        if not result["skipped"]:
            total_sents += result["total"]
            total_new += result["new"]
            total_failed += result["failed"]

    print(f"\n{'='*60}")
    print(f"📊 汇总：")
    print(f"  故事数：{len(story_files)}")
    print(f"  句子数：{total_sents}")
    print(f"  本次新生成：{total_new}")
    print(f"  失败：{total_failed}")
    if total_failed:
        print(f"\n⚠️  有 {total_failed} 句 TTS 失败，请检查 _audio_meta.json")
        sys.exit(1)
    print(f"\n✅ 完成")


if __name__ == "__main__":
    main()
