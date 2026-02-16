"""PDF 下载路由"""

import asyncio
import logging
import re
from io import BytesIO
from urllib.parse import quote
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from app.adapters import get_adapter
from app.schemas.novel import NovelSource

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_html(title: str, author: str, chapters: list[dict]) -> str:
    """将小说内容拼装为可渲染的 HTML 文档"""

    chapter_blocks: list[str] = []
    for ch in chapters:
        ch_title = ch.get("title", "")
        ch_content = ch.get("content", "")
        header = (
            f'<h2 style="margin-top:2em;margin-bottom:0.5em;color:#3a3a3a;border-bottom:1px solid #ddd;padding-bottom:4px;">{ch_title}</h2>'
            if ch_title
            else ""
        )
        chapter_blocks.append(f'{header}<div class="chapter">{ch_content}</div>')

    all_chapters = "\n".join(chapter_blocks)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  @page {{ margin: 2cm; }}
  body {{
    font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
    font-size: 14px;
    line-height: 1.9;
    color: #333;
    max-width: 100%;
  }}
  h1 {{
    text-align: center;
    font-size: 24px;
    margin-bottom: 4px;
  }}
  .author {{
    text-align: center;
    color: #888;
    margin-bottom: 2em;
    font-size: 13px;
  }}
  .chapter p {{
    text-indent: 2em;
    margin: 0.6em 0;
  }}
  .chapter img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
  }}
  .ao3-gap {{
    height: 0.6em;
  }}
</style>
</head>
<body>
  <h1>{title}</h1>
  <div class="author">作者：{author}</div>
  {all_chapters}
</body>
</html>"""


def _generate_pdf_sync(html: str) -> bytes:
    """用 Playwright 将 HTML 渲染为 PDF（同步，需在线程池中调用）"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        # 等待图片加载
        page.wait_for_timeout(2000)
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            margin={
                "top": "1.5cm",
                "bottom": "1.5cm",
                "left": "1.5cm",
                "right": "1.5cm",
            },
        )
        browser.close()
    return pdf_bytes


def _sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip() or "novel"


def _resolve_proxy_urls(html: str, base_url: str) -> str:
    """将相对代理 URL 转为绝对地址，使 Playwright 可加载图片"""
    # /api/proxy/... -> http://localhost:8000/api/proxy/...
    html = html.replace('src="/api/proxy/', f'src="{base_url}/api/proxy/')
    html = html.replace("src='/api/proxy/", f"src='{base_url}/api/proxy/")
    return html


@router.get("/{source}/{novel_id}")
async def download_novel_pdf(
    request: Request,
    source: NovelSource,
    novel_id: str,
    title: str = Query(default=""),
    author: str = Query(default=""),
):
    """下载小说为 PDF"""

    adapter = get_adapter(source)

    # 1. 获取小说详情（优先使用前端传来的 title/author）
    novel = None
    if not title or not author:
        try:
            novel = await adapter.get_detail(novel_id)
        except Exception:
            logger.warning(
                "Download: failed to get detail for %s/%s", source.value, novel_id
            )

    if not title:
        title = (novel.title if novel else None) or "未知标题"
    if not author:
        author = (novel.author if novel else None) or "未知作者"

    # 2. 获取章节列表
    try:
        chapter_list = await adapter.get_chapters(novel_id)
    except Exception:
        logger.exception("Download: failed to get chapters")
        chapter_list = []

    total_chapters = (
        len(chapter_list)
        if chapter_list
        else ((novel.chapter_count if novel else None) or 1)
    )

    # 3. 并发获取所有章节内容
    async def _fetch_chapter(i: int) -> dict:
        try:
            content = await adapter.get_chapter_content(novel_id, i)
            ch_title = ""
            if chapter_list and i - 1 < len(chapter_list):
                ch_title = chapter_list[i - 1].get("title", "")
            return {"title": ch_title, "content": content or ""}
        except Exception:
            logger.warning("Download: failed to get chapter %s", i)
            return {"title": f"第 {i} 章", "content": "<p>（章节内容获取失败）</p>"}

    chapters = list(
        await asyncio.gather(*[_fetch_chapter(i) for i in range(1, total_chapters + 1)])
    )

    if not chapters:
        raise HTTPException(status_code=404, detail="未找到任何章节内容")

    # 4. 生成 HTML 并转为 PDF
    html = _build_html(title, author, chapters)

    # 将相对代理 URL 转为绝对地址，使 Playwright 可加载图片
    base_url = str(request.base_url).rstrip("/")
    html = _resolve_proxy_urls(html, base_url)

    try:
        loop = asyncio.get_running_loop()
        pdf_bytes = await loop.run_in_executor(None, _generate_pdf_sync, html)
    except Exception:
        logger.exception("Download: PDF generation failed")
        raise HTTPException(status_code=500, detail="PDF 生成失败")

    # 5. 返回 PDF 文件
    filename = _sanitize_filename(f"{title} - {author}")
    encoded_filename = quote(f"{filename}.pdf")

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )
