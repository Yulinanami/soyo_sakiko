"""Lofter 动态抓取"""

import logging
from typing import List, Optional
from app.adapters.lofter_common import merge_novel_list, parse_cookie_header
from app.adapters.lofter_parse import parse_dwr_response, parse_tag_page_html
from app.adapters.playwright_helpers import (
    BROWSER_ARGS,
    DEFAULT_UA,
    ANTI_DETECT_SCRIPT,
    block_resources,
)
from app.config import settings
from app.schemas.novel import Novel

logger = logging.getLogger(__name__)


def search_dynamic_sync(
    tag: str,
    ranking_type: str,
    page_size: int,
    offset: int,
    exclude_tags: List[str],
    cookie: str,
    target_total: Optional[int] = None,
    return_all: bool = False,
) -> List[Novel]:
    """滚动页面获取更多结果"""
    if not settings.LOFTER_DYNAMIC_ENABLED:
        return []
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.warning("Lofter: Playwright not installed, skip dynamic crawl")
        return []

    try:
        from urllib.parse import quote

        encoded_tag = quote(tag, safe="")
        tag_path = "new" if ranking_type == "new" else "total"
        url = f"https://www.lofter.com/tag/{encoded_tag}/{tag_path}"

        headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if settings.LOFTER_CAPTTOKEN:
            headers["capttoken"] = settings.LOFTER_CAPTTOKEN

        if target_total is None:
            target_total = offset + page_size
        base_scrolls = settings.LOFTER_DYNAMIC_MAX_SCROLLS or 15
        # 更激进的滚动次数计算：确保深度分页时有足够滚动
        max_scrolls = max(base_scrolls, target_total // 5 + 10)
        scroll_wait_ms = settings.LOFTER_DYNAMIC_SCROLL_WAIT_MS or 1500
        initial_wait_ms = settings.LOFTER_DYNAMIC_INITIAL_WAIT_MS or 2000

        dwr_payloads: List[str] = []

        def on_response(response):
            """收集响应数据"""
            try:
                if "TagBean.search.dwr" in response.url:
                    dwr_payloads.append(response.text())
            except Exception:
                return

        with sync_playwright() as p:
            headless = True
            if not settings.LOFTER_DYNAMIC_HEADLESS:
                logger.info("Lofter: forcing headless mode to avoid browser popups")
            browser = p.chromium.launch(
                headless=headless,
                args=BROWSER_ARGS + ["--no-proxy-server"],
            )
            context = browser.new_context(
                user_agent=DEFAULT_UA,
                locale="zh-CN",
                extra_http_headers=headers,
            )
            context.add_init_script(ANTI_DETECT_SCRIPT)
            cookies = parse_cookie_header(cookie)
            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()
            # 拦截图片/字体/CSS，但保留 XHR (DWR 响应)
            page.route("**/*", block_resources)
            page.on("response", on_response)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except PWTimeout:
                pass
            try:
                page.wait_for_selector("div.m-mlist", timeout=20000)
            except PWTimeout:
                logger.warning("Lofter: tag page did not load list in time")
            page.wait_for_timeout(initial_wait_ms)

            ordered: List[Novel] = []
            index_map = {}
            processed_dwr = 0
            last_count = 0
            last_dwr = 0
            stable_rounds = 0
            scrolls = 0

            while (
                scrolls < max_scrolls
                and len(ordered) < target_total
                and stable_rounds < 6  # 从4放宽到6，减少提前停止
            ):
                html = page.content()
                parsed = parse_tag_page_html(
                    html, exclude_tags, ranking_type, limit=target_total
                )
                index_map = merge_novel_list(ordered, parsed, index_map)

                while processed_dwr < len(dwr_payloads):
                    payload = dwr_payloads[processed_dwr]
                    processed_dwr += 1
                    index_map = merge_novel_list(
                        ordered,
                        parse_dwr_response(payload, exclude_tags),
                        index_map,
                    )

                if len(ordered) == last_count:
                    if processed_dwr == last_dwr:
                        stable_rounds += 1
                    else:
                        stable_rounds = 0
                else:
                    stable_rounds = 0
                last_count = len(ordered)
                last_dwr = processed_dwr

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(scroll_wait_ms)
                scrolls += 1

            context.close()
            browser.close()

        while processed_dwr < len(dwr_payloads):
            payload = dwr_payloads[processed_dwr]
            processed_dwr += 1
            index_map = merge_novel_list(
                ordered,
                parse_dwr_response(payload, exclude_tags),
                index_map,
            )

        if not ordered:
            logger.warning("Lofter: dynamic crawl found 0 items")
        else:
            logger.info("Lofter: dynamic crawl collected %s items", len(ordered))

        if return_all:
            return ordered
        if offset >= len(ordered):
            return []
        return ordered[offset : offset + page_size]
    except Exception as e:
        logger.exception("Lofter dynamic crawl error")
        return []
