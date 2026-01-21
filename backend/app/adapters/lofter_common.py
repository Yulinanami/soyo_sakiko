"""Lofter 共享工具"""

import re
from typing import List
from app.adapters.utils import novel_key, sanitize
from app.schemas.novel import Novel


LOFTER_IMAGE_DOMAINS = [
    "lf127.net",
    "126.net",
    "lofter.com",
    "imglf",
    "nos.netease.com",
    "nosdn.127.net",
    "netease.com",
]


def parse_cookie_header(cookie: str) -> List[dict]:
    """解析登录信息"""
    cookies = []
    for part in cookie.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies.append(
            {
                "name": name,
                "value": value,
                "url": "https://www.lofter.com",
            }
        )
    return cookies


def extract_blog_name(url: str) -> str:
    """提取博客名"""
    if not url:
        return ""
    if url.startswith("//"):
        url = f"https:{url}"
    match = re.search(r"https?://([^/.]+)\.lofter\.com", url)
    return match.group(1) if match else ""


def extract_post_id(url: str) -> str:
    """提取文章编号"""
    if not url:
        return ""
    match = re.search(r"/post/([^/?#]+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/lpost/([^/?#]+)", url)
    if match:
        return match.group(1)
    return ""


def normalize_lofter_image_url(url: str) -> str:
    """规范化图片地址"""
    url = sanitize(url.strip()).replace("&amp;", "&")
    if url.startswith("//"):
        return f"https:{url}"
    return url


def proxy_lofter_images(html_content: str) -> str:
    """替换图片为转发地址"""
    from urllib.parse import quote

    try:
        from bs4 import BeautifulSoup
    except ImportError:

        def replace_img_src(match):
            """替换图片链接"""
            img_url = normalize_lofter_image_url(match.group(1))
            if any(domain in img_url for domain in LOFTER_IMAGE_DOMAINS):
                proxy_url = f"/api/proxy/lofter?url={quote(img_url, safe='')}"
                return f'src="{proxy_url}"'
            return match.group(0)

        result = re.sub(r'src="([^"]+)"', replace_img_src, html_content)
        result = re.sub(r"src='([^']+)'", replace_img_src, result)
        return result

    soup = BeautifulSoup(html_content, "html.parser")
    for img in soup.find_all("img"):
        raw_url = (
            img.get("large")
            or img.get("data-src")
            or img.get("data-original")
            or img.get("data-origin")
            or img.get("src")
        )
        parent = img.parent
        if parent and hasattr(parent, "attrs") and parent.attrs.get("bigimgsrc"):
            raw_url = parent.attrs.get("bigimgsrc") or raw_url
        if not raw_url:
            continue
        raw_url = normalize_lofter_image_url(raw_url)
        if any(domain in raw_url for domain in LOFTER_IMAGE_DOMAINS):
            img["src"] = f"/api/proxy/lofter?url={quote(raw_url, safe='')}"
        else:
            img["src"] = raw_url
        for attr in ["data-src", "data-original", "data-origin"]:
            if attr in img.attrs:
                del img.attrs[attr]
        if "large" in img.attrs:
            del img.attrs["large"]

    return str(soup)


def merge_novel_fields(existing: Novel, incoming: Novel) -> bool:
    """用新数据补全旧数据"""
    updated = False
    if not existing.cover_image and incoming.cover_image:
        existing.cover_image = incoming.cover_image
        updated = True
    if (not existing.title or existing.title == "无标题") and incoming.title:
        if incoming.title != "无标题":
            existing.title = incoming.title
            updated = True
    if (not existing.summary or existing.summary == "暂无简介") and incoming.summary:
        if incoming.summary != "暂无简介":
            existing.summary = incoming.summary
            updated = True
    if (not existing.author or existing.author == "Unknown") and incoming.author:
        if incoming.author != "Unknown":
            existing.author = incoming.author
            updated = True
    if (not existing.tags) and incoming.tags:
        existing.tags = incoming.tags
        updated = True
    return updated


def merge_novel_list(
    novels: List[Novel],
    incoming: List[Novel],
    index_map: dict | None = None,
) -> dict:
    """合并小说列表"""
    if index_map is None:
        index_map = {novel_key(n.source, n.id): idx for idx, n in enumerate(novels)}
    for novel in incoming:
        key = novel_key(novel.source, novel.id)
        idx = index_map.get(key)
        if idx is None:
            index_map[key] = len(novels)
            novels.append(novel)
        else:
            merge_novel_fields(novels[idx], novel)
    return index_map
