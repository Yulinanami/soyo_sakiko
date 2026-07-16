"""Playwright 共享配置和工具函数"""

import logging
import os
import shutil
import sys
from pathlib import Path


logger = logging.getLogger(__name__)

_SYSTEM_CHROMIUM_CHANNELS = ("chrome", "msedge")

_SYSTEM_CHROMIUM_COMMANDS = (
    "google-chrome",
    "google-chrome-stable",
    "chrome",
    "chrome.exe",
    "microsoft-edge",
    "microsoft-edge-stable",
    "msedge",
    "msedge.exe",
    "chromium",
    "chromium-browser",
    "chromium.exe",
    "brave-browser",
    "brave",
    "brave.exe",
    "vivaldi-stable",
    "vivaldi",
    "vivaldi.exe",
    "opera",
    "opera.exe",
)

_WINDOWS_CHROMIUM_PATHS = (
    ("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"),
    ("PROGRAMFILES(X86)", "Google/Chrome/Application/chrome.exe"),
    ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe"),
    ("PROGRAMFILES", "Microsoft/Edge/Application/msedge.exe"),
    ("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe"),
    ("LOCALAPPDATA", "Microsoft/Edge/Application/msedge.exe"),
    ("PROGRAMFILES", "Chromium/Application/chrome.exe"),
    ("LOCALAPPDATA", "Chromium/Application/chrome.exe"),
    ("PROGRAMFILES", "BraveSoftware/Brave-Browser/Application/brave.exe"),
    ("LOCALAPPDATA", "BraveSoftware/Brave-Browser/Application/brave.exe"),
    ("PROGRAMFILES", "Vivaldi/Application/vivaldi.exe"),
    ("LOCALAPPDATA", "Vivaldi/Application/vivaldi.exe"),
    ("LOCALAPPDATA", "Programs/Opera/launcher.exe"),
    ("LOCALAPPDATA", "Programs/Opera GX/launcher.exe"),
)

_MACOS_CHROMIUM_PATHS = (
    "Google Chrome.app/Contents/MacOS/Google Chrome",
    "Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "Chromium.app/Contents/MacOS/Chromium",
    "Brave Browser.app/Contents/MacOS/Brave Browser",
    "Vivaldi.app/Contents/MacOS/Vivaldi",
    "Opera.app/Contents/MacOS/Opera",
)

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
    """使用电脑上已经安装的 Chromium 系浏览器"""
    last_error = None

    for channel in _SYSTEM_CHROMIUM_CHANNELS:
        try:
            browser = browser_type.launch(channel=channel, **kwargs)
            logger.info("Playwright: using system browser channel %s", channel)
            return browser
        except Exception as exc:
            last_error = exc
            logger.debug(
                "Playwright: system browser channel %s unavailable: %s",
                channel,
                exc,
            )

    for executable_path in _system_chromium_executables():
        try:
            browser = browser_type.launch(
                executable_path=str(executable_path),
                **kwargs,
            )
            logger.info("Playwright: using system browser %s", executable_path)
            return browser
        except Exception as exc:
            last_error = exc
            logger.debug(
                "Playwright: system browser %s unavailable: %s",
                executable_path,
                exc,
            )

    raise RuntimeError(
        "未能启动电脑上已有的 Chromium 浏览器。请确认已安装 Chrome、Edge、"
        "Chromium、Brave、Vivaldi 或 Opera；本项目不会下载浏览器内核。"
    ) from last_error


def _system_chromium_executables():
    """查找 PATH 和系统常见安装目录中的 Chromium 浏览器"""
    candidates = []

    for command in _SYSTEM_CHROMIUM_COMMANDS:
        executable = shutil.which(command)
        if executable:
            candidates.append(Path(executable))

    if sys.platform == "win32":
        for environment, relative_path in _WINDOWS_CHROMIUM_PATHS:
            root = os.environ.get(environment)
            if root:
                candidates.append(Path(root) / relative_path)
    elif sys.platform == "darwin":
        for relative_path in _MACOS_CHROMIUM_PATHS:
            candidates.append(Path("/Applications") / relative_path)
            candidates.append(Path.home() / "Applications" / relative_path)

    seen = set()
    for candidate in candidates:
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        key = str(resolved).casefold() if sys.platform == "win32" else str(resolved)
        if key in seen:
            continue
        seen.add(key)
        yield resolved


def block_resources(route):
    """拦截不必要的资源请求（图片/字体/CSS/媒体），加速页面加载"""
    if route.request.resource_type in _BLOCKED_TYPES:
        route.abort()
    else:
        route.fallback()
