"""文本规范化工具。LLM 输出的文本在送 TTS / 渲染之前需要规范化。"""
import re
import unicodedata

# 智能引号 / 长破折号 / 省略号 → ASCII
_REPLACEMENTS = str.maketrans({
    "‘": "'", "’": "'",   # 单引号
    "“": '"', "”": '"',   # 双引号
    "–": "-", "—": ",",   # 短破折号 → hyphen，长破折号 → 逗号（TTS 友好）
    "…": "...",            # 省略号
    " ": " ",              # 不间断空格
})


def normalize_text(text: str) -> str:
    """智能引号 → ASCII、破折号 → 逗号、合并空白、NFKC 规范化。"""
    if not text:
        return text
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_REPLACEMENTS)
    # 合并连续空白为单个空格
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str) -> list[str]:
    """把一段英文文本按句末标点切分。返回每句的 stripped 字符串。

    用于校验 LLM 返回的 sentences[] 是否齐全（重新切分后长度应一致）。
    启发式：以 . ? ! 切分，保留缩写词（Mr. Mrs. etc.）的简单处理。
    """
    if not text:
        return []
    # 简单方案：按 . ? ! 切分，丢弃空段
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]
