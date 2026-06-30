"""mmx image generate 的 Python 封装。

调用方式：mmx image generate --prompt "..." --aspect-ratio 16:9 --out path.png
绕过 .cmd 包装器，直接调 node + mjs（避免 `#` 注释符问题）。
自动 retry 瞬时失败（exit 10 / timeout）由 mmx_retry.run_with_retry 提供。

设计原则：只暴露项目里实际用到的 3 个参数（prompt / aspect_ratio / out），
其他高级参数（seed / n / model / subject-ref 等）需要时通过 kwargs 透传。
"""
import shutil
import sys
from pathlib import Path
from typing import Any

from lib.mmx_retry import run_with_retry

# UTF-8 输出
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _find_mmx_invoke() -> tuple[list[str], str]:
    """与 mmx_speech / mmx_text 同款：绕过 .cmd 包装器直接调 node + mjs。"""
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


def generate_image(
    prompt: str,
    out_path: str | Path,
    *,
    aspect_ratio: str = "16:9",
    overwrite: bool = True,
    timeout: int = 180,
    **extra_args: Any,
) -> Path:
    """调用 mmx image generate 生成图片。

    Args:
        prompt: 图片描述文本
        out_path: 输出图片路径
        aspect_ratio: 宽高比 (e.g. "16:9", "1:1")。ignored if --width/--height 给出
        overwrite: 若 out_path 已存在是否覆盖（False 会传给 mmx 让其处理）
        timeout: 单次 attempt 超时秒数（总时间 ≈ timeout × 3 含重试）
        **extra_args: 其他 mmx image generate 支持的参数
            (e.g. seed=42, n=4, model="image-01", subject_ref="...")

    Returns:
        输出文件路径
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    args = [
        "image", "generate",
        "--prompt", prompt,
        "--aspect-ratio", aspect_ratio,
        "--out", str(out),
    ]
    # 透传额外参数（key 自动加 -- 前缀）
    for k, v in extra_args.items():
        if v is None:
            continue
        # 已是 -- 开头的直接用
        if k.startswith("--"):
            args.append(k)
            args.append(str(v))
        else:
            args.append(f"--{k.replace('_', '-')}")
            args.append(str(v))

    if not overwrite and out.exists():
        # mmx image generate 默认会覆盖；这里直接 skip
        return out

    run_with_retry(_MMX_INVOKE[0] + args, timeout=timeout)
    return out
