"""mmx CLI 调用的共享 retry 辅助。

mmx 在突发请求下会偶发 exit 10（rate limit / transient network），尤其
speech synthesize 和 image generate。直接抛 RuntimeError 让上游手动重试
既费时又容易漏。本模块提供 run_with_retry()，对 exit 10 和 TimeoutExpired
做指数退避（1s → 2s → 4s），其他非零退出码立刻抛错（说明是参数或模型问题，
retry 没用）。

应用到:
- mmx_speech.synthesize (TTS)
- mmx_text._run_mmx (LLM chat)
- mmx_image.generate_image (image generation, 见 mmx_image.py)
"""
import subprocess
import time
from typing import Sequence

# 已知"瞬时失败"的 exit code 集合（mmx 端限流 / 网络抖动）
# 其他非零退出 = 真错误（参数错、模型不存在、auth 失败等），不重试
_RETRYABLE_EXIT_CODES = {10}

DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 1.0  # 秒，1, 2, 4


def run_with_retry(
    cmd: Sequence[str],
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_base: float = DEFAULT_BACKOFF_BASE,
    timeout: int = 90,
    **subprocess_kwargs,
) -> subprocess.CompletedProcess:
    """Run a subprocess with exponential backoff on transient failures.

    Args:
        cmd: command + args
        max_retries: total attempts (1 = no retry; 3 = try up to 3 times)
        backoff_base: seconds; sleep = backoff_base * 2^attempt (1, 2, 4, ...)
        timeout: per-attempt subprocess timeout in seconds
        **subprocess_kwargs: extra kwargs passed to subprocess.run (e.g. cwd, env)

    Returns:
        subprocess.CompletedProcess (last successful one)

    Raises:
        RuntimeError: on non-retryable failure, or after all retries exhausted.
            The error message includes the full stderr of the LAST attempt.
        subprocess.TimeoutExpired: if the LAST attempt times out (transient
            TimeoutExpired in earlier attempts is silently retried).
    """
    last_result = None
    last_err = None
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                **subprocess_kwargs,
            )
        except subprocess.TimeoutExpired as e:
            last_err = f"timeout after {timeout}s"
            if attempt < max_retries - 1:
                _sleep(attempt, backoff_base, "timeout")
                continue
            raise

        if result.returncode == 0:
            return result

        last_result = result
        if result.returncode not in _RETRYABLE_EXIT_CODES:
            # 真错误（参数错、auth 错、模型错）—— 不重试
            raise RuntimeError(
                f"mmx 调用失败（exit {result.returncode}，非瞬时）\n"
                f"  cmd: {' '.join(cmd[:5])}...\n"
                f"  stderr: {result.stderr.strip()[:500]}"
            )

        last_err = f"exit {result.returncode}"
        if attempt < max_retries - 1:
            _sleep(attempt, backoff_base, f"exit {result.returncode}")

    # All retries exhausted
    stderr = (last_result.stderr.strip()[:500] if last_result is not None else "")
    raise RuntimeError(
        f"mmx 调用失败（重试 {max_retries} 次后放弃，最后一次 {last_err}）\n"
        f"  cmd: {' '.join(cmd[:5])}...\n"
        f"  stderr: {stderr}"
    )


def _sleep(attempt: int, backoff_base: float, reason: str) -> None:
    """Sleep with exponential backoff. Logs nothing (caller decides)."""
    delay = backoff_base * (2 ** attempt)
    time.sleep(delay)
