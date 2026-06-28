"""mmx text chat 的 Python 封装。

提供：
- chat()：单次调用，返回 LLM 响应文本
- chat_json()：调用并解析 JSON 输出，自动重试

依赖：`mmx` CLI 已安装（C:\\nvm4w\\nodejs\\mmx）。
环境变量：无需（M2.7 是默认 model）。
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# 强制 UTF-8 输出
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _find_mmx_invoke() -> tuple[list[str], str]:
    """定位 mmx 的调用方式。

    Windows 上 mmx.cmd 包装器会破坏带 `#`（cmd 注释符）或复杂引号的参数。
    因此绕过 .cmd，直接调 `node mmx.mjs`。这是最稳的调用方式。

    Returns:
        (prefix, label) - prefix 是要拼到 args 前面的命令前缀，label 是描述
    """
    # 找 node
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        # 兜底 nvm4w
        for cand in ["C:/nvm4w/nodejs/node.exe", "C:/Program Files/nodejs/node.exe"]:
            if Path(cand).exists():
                node = cand
                break
    if not node:
        raise FileNotFoundError("找不到 node 可执行文件")

    # 找 mmx.mjs
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
        raise FileNotFoundError(
            f"找不到 mmx-cli/dist/mmx.mjs。已尝试：{[str(c) for c in mjs_candidates]}"
        )

    return ([node, mjs], f"{Path(node).name} {Path(mjs).name}")


_MMX_INVOKE = _find_mmx_invoke()
MMX_BIN_LABEL = _MMX_INVOKE[1]


def _run_mmx(args: list[str], timeout: int = 300) -> str:
    """执行 mmx 子进程，返回 stdout。"""
    cmd = _MMX_INVOKE[0] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"mmx 调用失败（exit {result.returncode}）\n"
            f"  cmd: {' '.join(cmd[:5])}...\n"
            f"  stderr: {result.stderr.strip()[:500]}"
        )
    return result.stdout


def chat(
    messages: list[tuple[str, str]],
    *,
    model: str = "MiniMax-M2.7",
    max_tokens: int = 4000,
    temperature: float = 0.7,
    top_p: float = 0.9,
    timeout: int = 300,
) -> str:
    """调用 mmx text chat，返回响应文本。

    Args:
        messages: [(role, content), ...] 列表。role 可为 "system" / "user" / "assistant"。
        model: 模型名（默认 MiniMax-M2.7）。
        max_tokens: 最大生成 tokens。
        temperature: 采样温度（0-1）。
        top_p: nucleus sampling。
        timeout: 超时秒数。

    Returns:
        LLM 响应文本（清洗 markdown 围栏后的纯文本）。
    """
    args = [
        "text", "chat",
        "--model", model,
        "--max-tokens", str(max_tokens),
        "--temperature", str(temperature),
        "--top-p", str(top_p),
    ]
    for role, content in messages:
        args.extend(["--message", f"{role}:{content}"])

    raw = _run_mmx(args, timeout=timeout)
    return _extract_text(raw)


def chat_json(
    messages: list[tuple[str, str]],
    *,
    model: str = "MiniMax-M2.7",
    max_tokens: int = 4000,
    temperature: float = 0.7,
    top_p: float = 0.9,
    timeout: int = 300,
    max_parse_retries: int = 3,
) -> dict:
    """调用 mmx text chat 并解析 JSON 输出。

    如果 LLM 返回非纯 JSON（含 markdown 围栏、前后杂文），自动剥离并重试。
    最多重试 max_parse_retries 次。
    """
    last_err = None
    for attempt in range(max_parse_retries):
        text = chat(
            messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            timeout=timeout,
        )
        try:
            return _parse_json_response(text)
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            # 在 messages 末尾追加修复提示，让 LLM 重试
            messages = messages + [
                ("user", f"Your previous response could not be parsed as JSON. Error: {e}. "
                         f"Return ONLY the JSON object, no prose, no markdown fences, no comments.")
            ]
            time.sleep(1)
    raise RuntimeError(f"JSON 解析失败（重试 {max_parse_retries} 次后放弃）: {last_err}\n最后一次输出: {text[:500]}")


# ---------- 内部工具 ----------

_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _extract_text(raw: str) -> str:
    """从 mmx 的 JSON 输出里提取 assistant 文本。

    mmx (MiniMax Messages API) 的 content 数组结构：
    [
      {"thinking": "...", "type": "thinking"},
      {"text": "实际回复", "type": "text"}
    ]

    我们要提取所有 type=="text" 的块拼起来。
    也兼容 OpenAI 格式 (choices[0].message.content)。
    """
    raw = raw.strip()
    if not raw:
        return raw
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            # MiniMax 格式：content 是数组，找 type=="text" 的块
            if "content" in data and isinstance(data["content"], list):
                text_parts = []
                for block in data["content"]:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                if text_parts:
                    return "\n".join(text_parts)
                # 如果只有 thinking 没有 text，返回 thinking 内容（用于调试）
                thinking_parts = [
                    b.get("thinking", "") for b in data["content"]
                    if isinstance(b, dict) and b.get("type") == "thinking"
                ]
                if thinking_parts:
                    # 这里只返回 thinking 是为了让上层报错信息更清楚
                    return "[NO_TEXT_BLOCK]" + "\n".join(thinking_parts)
            # OpenAI 格式兼容
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
                    if isinstance(content, list):
                        text_parts = [
                            b.get("text", "") for b in content
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        return "\n".join(text_parts)
                    return content
                if "text" in choice:
                    return choice["text"]
            if "content" in data and isinstance(data["content"], str):
                return data["content"]
            if "text" in data and isinstance(data["text"], str):
                return data["text"]
        except json.JSONDecodeError:
            pass
    return raw


def _parse_json_response(text: str) -> dict:
    """从 LLM 响应文本中提取 JSON 对象。"""
    text = text.strip()
    if not text:
        raise ValueError("empty response")

    # 1) 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2) 去掉 markdown 围栏
    m = _FENCE_RE.match(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 3) 找第一个 { 到最后一个 } 的子串
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析 JSON：{e}\ntext: {text[:300]}")

    raise ValueError(f"响应中找不到 JSON 对象: {text[:300]}")
