#!/usr/bin/env python3
"""为单元和故事生成 AI 封面图（Identity V 风格）。

输出：data/covers/<theme_id>.png
- 16:9 比例，适合做卡片背景 / Hero banner
- 4 个故事各 1 张

用法：
  python scripts/generate_covers.py [--force]
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


REPO_ROOT = Path(__file__).resolve().parent.parent


def _find_mmx_invoke() -> list[str]:
    """与 mmx_text.py 一样绕过 .cmd 包装器，直接调 node + mjs。"""
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        for cand in ["C:/nvm4w/nodejs/node.exe", "C:/Program Files/nodejs/node.exe"]:
            if Path(cand).exists():
                node = cand
                break
    if not node:
        raise FileNotFoundError("找不到 node 可执行文件")
    mjs = Path("C:/nvm4w/nodejs/node_modules/mmx-cli/dist/mmx.mjs")
    if not mjs.exists():
        raise FileNotFoundError(f"找不到 {mjs}")
    return [node, str(mjs)]


_MMX_INVOKE = _find_mmx_invoke()


COVERS = [
    {
        "id": "magical-chocolate-factory",
        "prompt": "Identity V game style soft 3D anime illustration. A young female doctor with long dark hair wearing a doctor's coat (Doctor Emily Dyer) standing in a magical chocolate factory with golden chocolate rivers flowing around her, warm amber magical lighting, golden tickets floating in the air, dramatic shadows, painterly atmosphere, no text, no watermark",
    },
    {
        "id": "kind-barber",
        "prompt": "Identity V game style soft 3D anime illustration. A kind elderly barber with a white apron holding scissors next to a wooden counter with a colorful wig, in a vintage cozy barbershop with soft teal green lighting, warm gentle atmosphere, dramatic shadows, painterly, no text, no watermark",
    },
    {
        "id": "orpheus-mystery",
        "prompt": "Identity V game style soft 3D anime illustration. A young male detective with a long dark coat holding a magnifying glass (Detective Orpheus) examining mysterious letters scattered on an old wooden desk, in a dimly lit vintage post office, dark blue moody lighting, dramatic shadows, mysterious atmosphere, painterly, no text, no watermark",
    },
    {
        "id": "harsh-winter",
        "prompt": "Identity V game style soft 3D anime illustration. A young female gardener with brown hair (Emma Woods) and a princess in an elegant dress playing chess by a frost-covered window in a gothic manor, snowy winter night outside, icy blue moonlight streaming through the window, dramatic shadows, cold but warm-hearted atmosphere, painterly, no text, no watermark",
    },
]


def main():
    ap = argparse.ArgumentParser(description="生成 4 个故事的 Identity V 风格封面图")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default="image-01")
    args = ap.parse_args()

    out_dir = REPO_ROOT / "data" / "covers"
    out_dir.mkdir(parents=True, exist_ok=True)

    for cov in COVERS:
        out = out_dir / f"{cov['id']}.png"
        if out.exists() and not args.force:
            print(f"⏭️  {cov['id']}.png exists")
            continue
        print(f"🎨  生成 {cov['id']}.png ...")
        try:
            r = subprocess.run(
                _MMX_INVOKE + [
                    "image", "generate",
                    "--model", args.model,
                    "--prompt", cov["prompt"],
                    "--aspect-ratio", "16:9",
                    "--out", str(out),
                ],
                capture_output=True, text=True, timeout=180, encoding="utf-8", errors="replace",
            )
            if r.returncode == 0:
                print(f"  ✓ {cov['id']}.png saved")
            else:
                print(f"  ✗ {cov['id']} FAILED: {r.stderr.strip()[:200]}")
        except Exception as e:
            print(f"  ✗ {cov['id']} ERROR: {e}")


if __name__ == "__main__":
    main()
