"""Bilibili 数据整理"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.schemas.novel import Novel, NovelSource


def parse_article_summary(article: Dict[str, Any]) -> Optional[Novel]:
    """整理文章摘要信息"""
    article_id = str(article.get("id", ""))
    if not article_id:
        return None

    title = article.get("title", "")
    title = re.sub(r"<[^>]+>", "", title)

    mid = article.get("mid", "")
    author = article.get("uname", "") or article.get("author", "")
    if not author and mid:
        author = f"uid:{mid}"
    author_url = f"https://space.bilibili.com/{mid}" if mid else None

    summary = article.get("desc", "") or article.get("description", "")
    summary = re.sub(r"<[^>]+>", "", summary)

    tags = []
    category_name = article.get("category_name", "")
    if category_name:
        tags.append(category_name)

    view = article.get("view", 0)
    like = article.get("like", 0)

    pub_time = article.get("pub_time", 0)
    if pub_time:
        published_at = datetime.fromtimestamp(pub_time).isoformat()
    else:
        published_at = datetime.now().isoformat()

    cover = article.get("image_urls", [])
    cover_image = cover[0] if cover else None
    if not cover_image:
        origin_urls = article.get("origin_image_urls", [])
        cover_image = origin_urls[0] if origin_urls else None

    if cover_image and cover_image.startswith("//"):
        cover_image = "https:" + cover_image

    word_count = article.get("words", 0)

    return Novel(
        id=article_id,
        source=NovelSource.BILIBILI,
        title=title,
        author=author,
        author_url=author_url,
        summary=summary,
        tags=tags,
        rating=None,
        word_count=word_count if word_count else None,
        chapter_count=1,
        kudos=like,
        hits=view,
        published_at=published_at,
        updated_at=None,
        source_url=f"https://www.bilibili.com/read/cv{article_id}",
        cover_image=cover_image,
        is_complete=True,
    )


def parse_article_detail(
    article_data: Dict[str, Any], fallback_id: str
) -> Optional[Novel]:
    """整理文章详细信息"""
    if not article_data:
        return None

    article_id = str(article_data.get("id", fallback_id))
    title = article_data.get("title", "")
    author_info = article_data.get("author", {})
    author = author_info.get("name", "")
    mid = author_info.get("mid", "")
    author_url = f"https://space.bilibili.com/{mid}" if mid else None

    summary = article_data.get("summary", "")

    tags = []
    categories = article_data.get("categories", [])
    for cat in categories:
        if cat.get("name"):
            tags.append(cat["name"])

    actual_tags = article_data.get("tags", [])
    for tag_item in actual_tags:
        tag_name = (
            tag_item.get("name", "") if isinstance(tag_item, dict) else str(tag_item)
        )
        if tag_name and tag_name not in tags:
            tags.append(tag_name)

    stats = article_data.get("stats", {})
    view = stats.get("view", 0)
    like = stats.get("like", 0)

    pub_time = article_data.get("publish_time", 0)
    published_at = (
        datetime.fromtimestamp(pub_time).isoformat()
        if pub_time
        else datetime.now().isoformat()
    )

    cover_image = (
        article_data.get("banner_url", "") or article_data.get("image_urls", [""])[0]
        if article_data.get("image_urls")
        else None
    )
    if cover_image and cover_image.startswith("//"):
        cover_image = "https:" + cover_image

    word_count = article_data.get("words", 0)

    opus_data = article_data.get("opus", {})
    dynamic_id = opus_data.get("dynamic_id_str", "")

    if dynamic_id:
        source_url = f"https://www.bilibili.com/opus/{dynamic_id}"
    else:
        source_url = f"https://www.bilibili.com/read/cv{article_id}"

    return Novel(
        id=article_id,
        source=NovelSource.BILIBILI,
        title=title,
        author=author,
        author_url=author_url,
        summary=summary,
        tags=tags,
        rating=None,
        word_count=word_count if word_count else None,
        chapter_count=1,
        kudos=like,
        hits=view,
        published_at=published_at,
        updated_at=None,
        source_url=source_url,
        cover_image=cover_image,
        is_complete=True,
    )


def parse_opus_content(opus_data: Dict[str, Any]) -> str:
    """整理新格式内容"""
    html_parts: List[str] = []

    content = opus_data.get("content", {})
    paragraphs = content.get("paragraphs", [])

    for para in paragraphs:
        para_type = para.get("para_type")

        if para_type == 1:
            text_data = para.get("text", {})
            nodes = text_data.get("nodes", [])
            for node in nodes:
                word_data = node.get("word", {})
                words = word_data.get("words", "")
                if words:
                    words = words.replace("\n", "<br>")
                    html_parts.append(f"<p>{words}</p>")

        elif para_type == 2:
            pic_data = para.get("pic", {})
            pics = pic_data.get("pics", [])
            for pic in pics:
                pic_url = pic.get("url", "")
                if pic_url:
                    if pic_url.startswith("//"):
                        pic_url = "https:" + pic_url
                    html_parts.append(
                        f'<figure><img src="{pic_url}" alt="image" style="max-width:100%;"></figure>'
                    )

    return "".join(html_parts) if html_parts else ""


def rewrite_image_urls(content: str) -> str:
    """替换图片地址"""
    import urllib.parse

    def replace_url(match):
        """替换单个地址"""
        url = match.group(1)
        if url.startswith("//"):
            url = "https:" + url
        if "hdslb.com" in url or "bilibili.com" in url:
            proxy_url = f"/api/proxy/bilibili?url={urllib.parse.quote(url, safe='')}"
            return f'src="{proxy_url}"'
        return match.group(0)

    content = re.sub(r'src="([^"]+)"', replace_url, content)
    content = re.sub(r"src='([^']+)'", replace_url, content)

    return content


def parse_bilibili_content(content: str) -> str:
    """整理旧格式内容"""
    import json

    if content.startswith('{"ops"') or content.startswith("["):
        try:
            data = json.loads(content)
            if isinstance(data, dict) and "ops" in data:
                ops = data["ops"]
            elif isinstance(data, list):
                ops = data
            else:
                return content

            html_parts = []
            for op in ops:
                if isinstance(op, dict):
                    insert = op.get("insert", "")
                    if isinstance(insert, str):
                        text = insert.replace("\n\n", "</p><p>").replace("\n", "<br>")
                        html_parts.append(text)
                    elif isinstance(insert, dict):
                        if "image" in insert:
                            img_url = insert["image"]
                            html_parts.append(
                                f'<img src="{img_url}" alt="image" style="max-width:100%;">'
                            )

            content = "<p>" + "".join(html_parts) + "</p>"
            content = re.sub(r"<p>\s*</p>", "", content)
            content = re.sub(r"<br>\s*<br>", "</p><p>", content)
            return content
        except json.JSONDecodeError:
            pass

    if "<" in content and ">" in content:
        return content

    paragraphs = content.split("\n\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if p:
            p = p.replace("\n", "<br>")
            html_parts.append(f"<p>{p}</p>")

    return "".join(html_parts) if html_parts else f"<p>{content}</p>"
