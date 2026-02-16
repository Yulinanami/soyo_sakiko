"""Playwright 共享配置和工具函数"""

BROWSER_ARGS = ["--disable-blink-features=AutomationControlled"]

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

ANTI_DETECT_SCRIPT = (
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
)

# 不需要加载的资源类型 — 只需要 HTML 文本
_BLOCKED_TYPES = frozenset({"image", "font", "stylesheet", "media"})


def block_resources(route):
    """拦截不必要的资源请求（图片/字体/CSS/媒体），加速页面加载"""
    if route.request.resource_type in _BLOCKED_TYPES:
        route.abort()
    else:
        route.fallback()
