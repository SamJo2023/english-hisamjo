"""mmx speech synthesize 的 Python 封装。

调用方式：mmx speech synthesize --text "..." --out file.mp3
绕过 .cmd 包装器，直接调 node + mjs（避免 `#` 注释符问题）。
自动 retry 瞬时失败（exit 10 / timeout）由 mmx_retry.run_with_retry 提供。
"""
import shutil
import sys
from pathlib import Path

from lib.mmx_retry import run_with_retry

# UTF-8 输出
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _find_mmx_invoke() -> tuple[list[str], str]:
    """与 mmx_text.py 同款：绕过 .cmd 包装器直接调 node + mjs。"""
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        for cand in ["C:/nvm4w/nodejs/node.exe", "C:/Program Files/nodejs/node.exe"]:
            if Path(cand).exists():
                node = cand
                break
    if not node:
        raise FileNotFoundError("找不到 node 可执行文件")

    mjs_candidates = [
        Path("C:/nvm4w/nodejs/node_modules/mmx-cli/dist/mmx.mjs"),
        Path(__file__).resolve().parent.parent.parent / "node_modules" / "mmx-cli" / "dist" / "mmx.mjs",
    ]
    mjs = None
    for c in mjs_candidates:
        if c.exists():
            mjs = str(c)
            break
    if not mjs:
        raise FileNotFoundError("找不到 mmx-cli/dist/mmx.mjs")

    return ([node, mjs], f"{Path(node).name} {Path(mjs).name}")


_MMX_INVOKE = _find_mmx_invoke()


def synthesize(
    text: str,
    out_path: str | Path,
    *,
    voice: str = "tianxin_xiaoling",
    model: str = "speech-2.8-hd",
    speed: float = 1.0,
    sample_rate: int = 32000,
    bitrate: int = 128000,
    timeout: int = 90,
) -> Path:
    """调用 mmx speech synthesize 生成 mp3。

    Args:
        text: 要合成语音的文本（英文/中文均可）
        out_path: 输出 mp3 文件路径
        voice: 音色 ID（默认 tianxin_xiaoling）
        model: TTS 模型（默认 speech-2.8-hd）
        speed: 语速倍数（0.5-2.0，默认 1.0）
        sample_rate: 采样率 Hz（默认 32000）
        bitrate: 比特率 bps（默认 128000）
        timeout: 单次调用超时秒数（每次 attempt；总时间 ≈ timeout × 3）

    Returns:
        输出文件路径
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    args = [
        "speech", "synthesize",
        "--text", text,
        "--voice", voice,
        "--model", model,
        "--speed", str(speed),
        "--sample-rate", str(sample_rate),
        "--bitrate", str(bitrate),
        "--format", "mp3",
        "--out", str(out),
    ]

    run_with_retry(_MMX_INVOKE[0] + args, timeout=timeout)
    return out

