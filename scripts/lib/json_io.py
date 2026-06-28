"""JSON I/O 工具，统一 schema_version 处理。

所有 vocab.json / story.json / meta.json 都用这套函数读写。
"""
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


def read_json(path: str | Path) -> dict:
    """读取 JSON 文件，schema_version 校验。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSON not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    _check_schema(data, p)
    return data


def write_json(path: str | Path, data: dict, *, indent: int = 2) -> None:
    """写入 JSON 文件，自动补 schema_version 字段。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if "schema_version" not in data:
        data = {**data, "schema_version": SCHEMA_VERSION}
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
        f.write("\n")


def _check_schema(data: Any, path: Path) -> None:
    """轻量 schema 检查：要求有 schema_version 字段且是 int。"""
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a dict, got {type(data).__name__}")
    sv = data.get("schema_version")
    if sv is None:
        raise ValueError(f"{path}: missing schema_version")
    if not isinstance(sv, int):
        raise ValueError(f"{path}: schema_version must be int, got {type(sv).__name__}")
    if sv > SCHEMA_VERSION:
        raise ValueError(
            f"{path}: schema_version={sv} is newer than supported ({SCHEMA_VERSION}). "
            f"请升级 scripts/lib/json_io.py 或检查文件来源。"
        )
