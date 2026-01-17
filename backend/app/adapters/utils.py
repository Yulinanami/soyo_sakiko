"""
Adapter utilities.
"""

import re
from typing import Any, Iterable


_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


def decode_unicode(text: str) -> str:
    """Decode Unicode escape sequences like \\u53EA."""
    if not text:
        return text

    def replace_unicode(match):
        try:
            return chr(int(match.group(1), 16))
        except Exception:
            return match.group(0)

    return re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode, text)


def sanitize(text: str) -> str:
    """Normalize text by decoding \\u escapes and removing surrogates."""
    if not text:
        return text
    text = decode_unicode(text)
    return _SURROGATE_RE.sub("", text)


def sanitize_html(html: str) -> str:
    """Strip surrogate pairs from HTML without decoding escapes."""
    if not html:
        return html
    return _SURROGATE_RE.sub("", html)


def exclude(text: str, patterns: Iterable[str]) -> bool:
    """Return True when text contains any pattern."""
    if not text:
        return False
    for pattern in patterns or []:
        if pattern and pattern in text:
            return True
    return False


def to_iso_date(date_val: Any) -> str:
    if date_val is None:
        return ""
    try:
        if hasattr(date_val, "isoformat"):
            return date_val.isoformat()
        return str(date_val)
    except Exception:
        return ""


def novel_key(source: Any, novel_id: Any) -> str:
    return f"{source}:{novel_id}"
