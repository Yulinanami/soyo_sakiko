"""AO3 动态抓取 (Playwright)"""

import logging
from typing import List, Optional
from urllib.parse import quote
from app.config import settings
from app.schemas.novel import Novel
from app.adapters.playwright_helpers import (
    BROWSER_ARGS,
    DEFAULT_UA,
    ANTI_DETECT_SCRIPT,
    block_resources,
)

logger = logging.getLogger(__name__)


def build_search_url(tags: List[str], sort_column: str, page: int) -> str:
    """构建 AO3 搜索 URL"""
    # 抽取对名标签 (包含 /) 和普通标签
    rel_tags = [t for t in tags if "/" in t]
    any_tags = [t for t in tags if "/" not in t]

    # 构建查询参数
    any_query = quote(" OR ".join(f"{t}" for t in any_tags)) if any_tags else ""
    rel_query = quote(",".join(rel_tags)) if rel_tags else ""

    base_url = "https://archiveofourown.org/works/search"
    query_parts = [
        "commit=Search",
        f"work_search[query]={any_query}",
        f"work_search[relationship_names]={rel_query}",
        f"work_search[sort_column]={sort_column}",
        f"work_search[sort_direction]=desc",
        f"page={page}",
    ]

    return f"{base_url}?{'&'.join(query_parts)}"


def _launch_context(p):
    """创建统一配置的浏览器和上下文"""
    browser = p.chromium.launch(headless=True, args=BROWSER_ARGS)
    context = browser.new_context(user_agent=DEFAULT_UA, locale="zh-CN")
    context.add_init_script(ANTI_DETECT_SCRIPT)
    return browser, context


def _new_page_with_blocking(context):
    """创建页面并启用资源拦截"""
    page_obj = context.new_page()
    page_obj.route("**/*", block_resources)
    return page_obj


def search_dynamic_sync(
    tags: List[str],
    sort_column: str,
    page: int,
) -> str:
    """使用 Playwright 抓取 AO3 单页搜索页 HTML"""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.error("AO3: Playwright not installed")
        return ""

    url = build_search_url(tags, sort_column, page)
    logger.info(f"AO3: Fetching {url}")

    try:
        with sync_playwright() as p:
            browser, context = _launch_context(p)
            page_obj = _new_page_with_blocking(context)

            page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

            try:
                page_obj.wait_for_selector("li.work.blurb.group", timeout=15000)
            except PWTimeout:
                logger.warning("AO3: No results or page load timeout")
                if "No results found" in page_obj.content():
                    context.close()
                    browser.close()
                    return "EMPTY"

            html = page_obj.content()

            context.close()
            browser.close()
            return html

    except Exception as e:
        logger.error(f"AO3: Dynamic crawl failed: {e}")
        return ""


def search_multi_pages_sync(
    tags: List[str],
    sort_column: str,
    start_page: int,
    max_pages: int = 3,
) -> List[str]:
    """复用一个浏览器实例抓取多页 AO3 搜索结果"""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.error("AO3: Playwright not installed")
        return []

    pages_html: List[str] = []

    try:
        with sync_playwright() as p:
            browser, context = _launch_context(p)
            page_obj = _new_page_with_blocking(context)

            for pg in range(start_page, start_page + max_pages):
                url = build_search_url(tags, sort_column, pg)
                logger.info(f"AO3: Fetching page {pg}: {url}")

                page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

                try:
                    page_obj.wait_for_selector("li.work.blurb.group", timeout=15000)
                except PWTimeout:
                    logger.warning(f"AO3: No results on page {pg}")
                    if "No results found" in page_obj.content():
                        break

                html = page_obj.content()
                if not html:
                    break
                pages_html.append(html)

            context.close()
            browser.close()

    except Exception as e:
        logger.error(f"AO3: Multi-page crawl failed: {e}")

    return pages_html


def get_work_details_dynamic_sync(
    work_id: str, chapter_num: Optional[int] = None
) -> dict:
    """使用 Playwright 抓取 AO3 作品详情或章节内容"""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.error("AO3: Playwright not installed")
        return {}

    # 使用 view_adult=true 绕过成年限制
    url = f"https://archiveofourown.org/works/{work_id}?view_adult=true"

    logger.info(f"AO3: Fetching work detail {url}")

    try:
        with sync_playwright() as p:
            browser, context = _launch_context(p)
            page_obj = _new_page_with_blocking(context)

            page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 等待内容加载
            try:
                page_obj.wait_for_selector("#workskin", timeout=15000)
            except PWTimeout:
                pass

            # 如果需要具体章节内容
            chapter_content = ""
            if chapter_num:
                chapter_url = f"https://archiveofourown.org/works/{work_id}/chapters/{chapter_num}?view_adult=true"
                page_obj.goto(chapter_url, wait_until="domcontentloaded", timeout=30000)
                try:
                    page_obj.wait_for_selector("#workskin", timeout=10000)
                except Exception:
                    pass

                # 获取完整内容 (包括作品级别的前言/后记和章节内容)
                chapter_content = page_obj.evaluate(
                    """() => {
                    const workskin = document.querySelector('#workskin');
                    return workskin ? workskin.innerHTML : '';
                }"""
                )
                # 获取该页的完整 HTML 以便解析 metadata
                html = page_obj.content()
            else:
                # 获取主页完整内容（包含作品前言）
                html = page_obj.content()
                chapter_content = page_obj.evaluate(
                    """() => {
                    const workskin = document.querySelector('#workskin');
                    return workskin ? workskin.innerHTML : '';
                }"""
                )

            # 获取章节列表 (如果有选择框)
            chapters = []
            chapter_els = page_obj.query_selector_all("select#selected_id option")
            if chapter_els:
                for i, el in enumerate(chapter_els, 1):
                    chapters.append(
                        {"number": i, "title": el.inner_text() or f"Chapter {i}"}
                    )
            else:
                # 单章节作品
                chapters.append({"number": 1, "title": "Chapter 1"})

            context.close()
            browser.close()

            return {
                "html": html,
                "chapters": chapters,
                "chapter_content": chapter_content,
            }

    except Exception as e:
        logger.error(f"AO3: Dynamic detail fetch failed: {e}")
        return {}
