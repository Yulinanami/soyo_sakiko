"""适配器工具"""

import re
import time
from typing import Any, Callable, Iterable, List, Optional, Tuple, Type


_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


def decode_unicode(text: str) -> str:
    """把转义字符转成文字"""
    if not text:
        return text

    def replace_unicode(match):
        """替换一个转义片段"""
        try:
            return chr(int(match.group(1), 16))
        except Exception:
            return match.group(0)

    return re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode, text)


def sanitize(text: str) -> str:
    """清理文本内容"""
    if not text:
        return text
    text = decode_unicode(text)
    # 移除可能残留的 HTML 标签（如双重编码的 &amp;lt;p&amp;gt; 解码后）
    text = re.sub(r"<[^>]*>?", "", text)
    return _SURROGATE_RE.sub("", text).strip()


def sanitize_html(html: str) -> str:
    """清理网页内容里的异常字符"""
    if not html:
        return html
    return _SURROGATE_RE.sub("", html)


def exclude(text: str, patterns: Iterable[str]) -> bool:
    """判断文本是否包含排除词"""
    if not text:
        return False
    text_lower = text.lower()
    for pattern in patterns or []:
        if pattern and pattern.lower() in text_lower:
            return True
    return False


def exclude_any_tag(tags: List[str], exclude_patterns: Iterable[str]) -> bool:
    """判断标签是否命中排除词"""
    if not tags:
        return False
    for tag in tags:
        if not tag:
            continue
        tag_lower = tag.lower()
        for pattern in exclude_patterns or []:
            if pattern and pattern.lower() in tag_lower:
                return True
    return False


def to_iso_date(date_val: Any) -> str:
    """转换时间为字符串"""
    if date_val is None:
        return ""
    try:
        if hasattr(date_val, "isoformat"):
            return date_val.isoformat()
        return str(date_val)
    except Exception:
        return ""


def novel_key(source: Any, novel_id: Any) -> str:
    """生成小说标识"""
    return f"{source}:{novel_id}"


def with_retries(
    func: Callable[[], Any],
    *,
    retries: int = 2,
    base_delay: float = 0.6,
    max_delay: float = 2.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    on_retry: Optional[Callable[[BaseException, int], None]] = None,
) -> Any:
    """失败后再次执行"""
    last_error: Optional[BaseException] = None
    for attempt in range(retries + 1):
        try:
            return func()
        except exceptions as exc:
            last_error = exc
            if attempt >= retries:
                break
            if on_retry:
                on_retry(exc, attempt + 1)
            delay = min(base_delay * (2**attempt), max_delay)
            time.sleep(delay)
    if last_error:
        raise last_error
    return func()
