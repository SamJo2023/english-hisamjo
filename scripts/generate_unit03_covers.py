#!/usr/bin/env python3
"""为 Unit03 补 3 张缺失的封面图。

Unit03 4 个主题：the-chinese-restaurant / cooking-class / food-and-health / review。
review.png 已存在（与 Unit02 review 共用），所以只生成前 3 张。

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
    print(f"\n✅ 完成。共生成 {len(COVERS)} 张 Unit03 封面。")


if __name__ == "__main__":
    main()