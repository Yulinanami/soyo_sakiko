"""AO3 动态抓取 (Playwright)"""

import logging
from typing import List, Optional
from urllib.parse import quote
from app.config import settings
from app.schemas.novel import Novel

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


def search_dynamic_sync(
    tags: List[str],
    sort_column: str,
    page: int,
) -> str:
    """使用 Playwright 抓取 AO3 搜索页 HTML"""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.error("AO3: Playwright not installed")
        return ""

    url = build_search_url(tags, sort_column, page)
    logger.info(f"AO3: Fetching {url}")

    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=True, args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="zh-CN",
            )

            # 反检测
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

            page_obj = context.new_page()

            # 访问页面
            page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 等待列表加载
            try:
                page_obj.wait_for_selector("li.work.blurb.group", timeout=15000)
            except PWTimeout:
                logger.warning("AO3: No results or page load timeout")
                # 检查是否是 404 或者空结果页面
                if "No results found" in page_obj.content():
                    return "EMPTY"

            html = page_obj.content()

            context.close()
            browser.close()
            return html

    except Exception as e:
        logger.error(f"AO3: Dynamic crawl failed: {e}")
        return ""


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
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page_obj = context.new_page()
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
                except:
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
