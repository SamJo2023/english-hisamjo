#!/usr/bin/env python3
"""为 Unit03 补 4 张封面图。

Unit03 4 个主题：the-chinese-restaurant / cooking-class / food-and-health / review。
- 前 3 张是新主题（之前不存在）
- unit03-review.png 是 Unit03 review 专属封面（与 Unit02 review.png 区分）
  通过 planner.review.cover_id 字段指向。Unit02 review 保持 review.png。

风格沿用 scripts/generate_covers.py 的 Identity V 3D anime 风格。
"""
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))
from lib.mmx_image import generate_image  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "covers"


COVERS = [
    {
        # theme_class: mystery
        "id": "the-chinese-restaurant",
        "prompt": (
            "Identity V game style soft 3D anime illustration. "
            "A young male detective with a long dark coat holding a magnifying glass "
            "(Detective Orpheus) and a mercenary with a sharp gaze (Mercenary Naidu) "
            "standing at the entrance of a mysterious Chinese restaurant at night. "
            "Red paper lanterns glowing warmly, bamboo steamers stacked on tables, "
            "ornate wooden door with golden handles, dark crimson and gold tones, "
            "mysterious atmosphere with curling incense smoke, dramatic shadows, "
            "painterly, no text, no watermark"
        ),
    },
    {
        # theme_class: encouragement
        "id": "cooking-class",
        "prompt": (
            "Identity V game style soft 3D anime illustration. "
            "A warm cozy kitchen classroom with golden afternoon light. "
            "A young female doctor with long dark hair wearing a doctor's coat "
            "(Doctor Emily Dyer) is teaching a cheerful young woman (Emma Woods) "
            "and a curious student (Naidu) how to cook. Fresh vegetables, a wooden "
            "cutting board, a steaming pot on a vintage stove, copper pots hanging, "
            "warm amber and cream tones, encouraging and joyful atmosphere, "
            "dramatic shadows, painterly, no text, no watermark"
        ),
    },
    {
        # theme_class: choice
        "id": "food-and-health",
        "prompt": (
            "Identity V game style soft 3D anime illustration. "
            "A young female doctor with long dark hair in a doctor's coat "
            "(Doctor Emily Dyer) holding a plate of fresh green salad next to "
            "a worried patient holding their stomach, in a bright clean clinic "
            "room with soft sunlight. On one side a hamburger and chips "
            "(representing unhealthy choice), on the other side a salad bowl "
            "and fresh vegetables (representing healthy choice). "
            "Soft mint green and warm cream tones, gentle caring atmosphere, "
            "dramatic shadows, painterly, no text, no watermark"
        ),
    },
    {
        # theme_class: review (Unit03 specific: 在庄园 / At the Manor — Orpheus at dining table)
        # Filename 是 unit03-review（不是 review），因为 Unit02 已经占了 review.png。
        # render.py 会从 planner 的 review.cover_id 字段读这个值。
        "id": "unit03-review",
        "prompt": (
            "Identity V game style soft 3D anime illustration. "
            "A young male detective with a long dark coat (Detective Orpheus) "
            "sitting alone at a long wooden dining table in a grand old manor. "
            "An evening menu sits on a plate in front of him, a half-eaten "
            "bowl of soup and a sandwich. Warm candlelight glowing from a "
            "silver candelabra, a fireplace in the background, large gothic "
            "windows showing dusk outside. Reflections of Chinese lanterns "
            "and Western pastries subtly visible in the polished silverware. "
            "Warm amber, soft gold, and gentle crimson tones, contemplative "
            "and peaceful atmosphere, dramatic shadows, painterly, "
            "no text, no watermark"
        ),
    },
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for cov in COVERS:
        out = OUT_DIR / f"{cov['id']}.png"
        if out.exists():
            print(f"⏭️  {cov['id']}.png already exists")
            continue
        print(f"🎨  生成 {cov['id']}.png ...")
        try:
            generate_image(
                prompt=cov["prompt"],
                out_path=out,
                aspect_ratio="16:9",
                model="image-01",
            )
            print(f"  ✓ {cov['id']}.png saved")
        except Exception as e:
            print(f"  ✗ {cov['id']} ERROR: {e}")
            sys.exit(1)
    print(f"\n✅ 完成。共 {len(COVERS)} 张 Unit03 封面（已存在的会 skip）。")


if __name__ == "__main__":
    main()