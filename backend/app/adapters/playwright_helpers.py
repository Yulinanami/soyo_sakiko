"""Playwright 共享配置和工具函数"""

import logging


logger = logging.getLogger(__name__)

_SYSTEM_CHROMIUM_CHANNELS = ("chrome", "msedge")

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


def launch_browser(browser_type, **kwargs):
    """优先使用本机 Chromium 系浏览器，失败时回退 Playwright Chromium"""
    for channel in _SYSTEM_CHROMIUM_CHANNELS:
        try:
            browser = browser_type.launch(channel=channel, **kwargs)
            logger.info("Playwright: using system browser channel %s", channel)
            return browser
        except Exception as exc:
            logger.debug(
                "Playwright: system browser channel %s unavailable: %s",
                channel,
                exc,
            )

    logger.info("Playwright: falling back to bundled Chromium")
    return browser_type.launch(**kwargs)


def block_resources(route):
    """拦截不必要的资源请求（图片/字体/CSS/媒体），加速页面加载"""
    if route.request.resource_type in _BLOCKED_TYPES:
        route.abort()
    else:
        route.fallback()
