"""
Lofter parsing helpers.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional

from app.adapters.utils import decode_unicode, exclude, exclude_any_tag, sanitize
from app.schemas.novel import Novel, NovelSource
from app.adapters.lofter_common import (
    extract_blog_name,
    extract_post_id,
    normalize_lofter_image_url,
)

logger = logging.getLogger(__name__)


def parse_tag_page_html(
    html: str,
    exclude_tags: List[str],
    ranking_type: str,
    limit: Optional[int] = None,
) -> List[Novel]:
    """Parse tag page HTML into novel list."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div.m-mlist")

    novels: List[Novel] = []
    seen_ids = set()
    for item in items:
        author_el = item.select_one(".publishernick")
        author = sanitize(author_el.get_text(strip=True)) if author_el else "Unknown"
        author_url = author_el.get("href") if author_el else ""
        if author_url and author_url.startswith("//"):
            author_url = f"https:{author_url}"

        post_link_el = item.select_one(".isayt a.isayc")
        post_link = post_link_el.get("href") if post_link_el else ""
        if not post_link:
            link = item.select_one('a[href*="/post/"]')
            post_link = link.get("href") if link else ""
        if post_link and post_link.startswith("//"):
            post_link = f"https:{post_link}"
        if not post_link:
            continue

        blog_name = extract_blog_name(author_url or post_link)
        post_id = extract_post_id(post_link)
        if not post_id:
            continue
        if not blog_name:
            continue
        novel_id = f"{blog_name}:{post_id}"
        if novel_id in seen_ids:
            continue
        seen_ids.add(novel_id)

        title = ""
        title_el = item.select_one(".m-long-post-icnt .tit")
        if title_el:
            title = sanitize(title_el.get_text(strip=True))
        if not title:
            title_el = item.select_one(
                ".m-icnt .ttl, .m-icnt .title, .m-icnt .tit, .m-icnt h3, .m-icnt h2"
            )
            if title_el:
                title = sanitize(title_el.get_text(strip=True))
        if not title and post_link_el:
            title = sanitize(
                post_link_el.get("data-title")
                or post_link_el.get("title")
                or post_link_el.get_text(strip=True)
                or ""
            )
        if not title:
            for attr in ("data-title", "data-tit", "data-name", "title"):
                raw = item.get(attr) if hasattr(item, "get") else ""
                if raw:
                    title = sanitize(raw)
                    break

        summary = ""
        pre_el = item.select_one(".m-long-post-icnt .pre")
        if pre_el:
            summary = sanitize(pre_el.get_text(strip=True))
        if not summary:
            txt_el = item.select_one(".m-icnt .txt")
            if txt_el:
                summary = sanitize(txt_el.get_text(strip=True))

        tags = [
            sanitize(t.get_text(strip=True))
            for t in item.select(".w-opt .opta a span")
            if t.get_text(strip=True)
        ]

        if title and exclude(title, exclude_tags):
            continue
        # Also filter by actual tags
        if exclude_any_tag(tags, exclude_tags):
            continue

        kudos = None
        opt_text = item.get_text(" ", strip=True)
        hot_match = re.search(r"热度\((\d+)\)", opt_text)
        if hot_match:
            kudos = int(hot_match.group(1))

        published_at = datetime.now().isoformat()
        title_attr = post_link_el.get("title", "") if post_link_el else ""
        date_match = re.search(r"(\d{2})/(\d{2})\s+(\d{2}:\d{2})", title_attr)
        if date_match:
            month, day, hm = date_match.groups()
            try:
                published_at = datetime(
                    datetime.now().year,
                    int(month),
                    int(day),
                    int(hm[:2]),
                    int(hm[3:]),
                ).isoformat()
            except Exception:
                pass

        cover_image = None
        img_el = item.select_one(".m-icnt img") or item.select_one("img")
        if img_el:
            cover_image = (
                img_el.get("large")
                or img_el.get("data-src")
                or img_el.get("data-original")
                or img_el.get("data-origin")
                or img_el.get("data-img")
                or img_el.get("data-cover")
                or img_el.get("src")
            )
        if not cover_image:
            for attr in (
                "data-cover",
                "data-img",
                "data-origin",
                "data-original",
                "data-src",
                "data-image",
                "data-thumb",
            ):
                raw = item.get(attr) if hasattr(item, "get") else ""
                if raw:
                    cover_image = raw
                    break
        if not cover_image:
            for el in item.select('[style*="background"]'):
                style = el.get("style") or ""
                match = re.search(r"background-image\\s*:\\s*url\\(([^)]+)\\)", style)
                if match:
                    cover_image = match.group(1).strip("\"'")
                    break
        if cover_image:
            cover_image = normalize_lofter_image_url(cover_image)
            if cover_image.startswith("data:"):
                cover_image = None
            elif cover_image.startswith("./") or cover_image.startswith("/"):
                cover_image = None

        novel = Novel(
            id=novel_id,
            source=NovelSource.LOFTER,
            title=title if title else "无标题",
            author=author,
            author_url=author_url
            or (f"https://{blog_name}.lofter.com" if blog_name else ""),
            summary=summary[:500] if summary else "暂无简介",
            tags=tags[:10],
            word_count=None,
            chapter_count=1,
            kudos=kudos,
            hits=None,
            rating=None,
            published_at=published_at,
            updated_at=published_at,
            source_url=post_link,
            cover_image=cover_image,
            is_complete=True,
        )
        novels.append(novel)

    if ranking_type == "total":
        novels.sort(key=lambda n: n.kudos or 0, reverse=True)

    if limit:
        return novels[:limit]
    return novels


def parse_dwr_response(response_text: str, exclude_tags: List[str]) -> List[Novel]:
    """Parse DWR response format."""
    novels = []

    try:
        # DWR returns JavaScript code, extract assignments first
        assignments = {}

        # Match variable assignments like s0.xxx=yyy
        var_pattern = re.compile(r"s(\d+)\.(\w+)\s*=\s*([^;]+);")
        for match in var_pattern.finditer(response_text):
            var_id, prop, value = match.groups()
            key = f"s{var_id}"
            if key not in assignments:
                assignments[key] = {}
            assignments[key][prop] = strip_quotes(value)

        # Match string values
        str_pattern = re.compile(r's(\d+)\.(\w+)\s*=\s*"([^"]*)"')
        for match in str_pattern.finditer(response_text):
            var_id, prop, value = match.groups()
            key = f"s{var_id}"
            if key not in assignments:
                assignments[key] = {}
            assignments[key][prop] = value

        # Find posts by post references if present; else fall back to post-like objects
        post_candidates = []
        post_refs = re.findall(r"s(\d+)\.post=s(\d+);", response_text)
        if post_refs:
            for _, post_id in post_refs:
                post_key = f"s{post_id}"
                if post_key in assignments:
                    post_candidates.append((post_key, assignments[post_key]))
        else:
            for key, data in assignments.items():
                if looks_like_post(data):
                    post_candidates.append((key, data))

        logger.info("Lofter DWR: found %s post candidates", len(post_candidates))

        parsed_count = 0
        skipped_no_url = 0
        skipped_no_blog = 0
        seen_ids = set()

        for _, post in post_candidates:
            # Get title and decode Unicode escapes
            title = post.get("title", "")
            title = sanitize(title) if title else ""
            if not title:
                # Try to get from digest
                digest = post.get("digest", "")
                title = sanitize(clean_html(digest))[:50] if digest else "无标题"

            # Check exclude tags
            if exclude(title, exclude_tags):
                continue

            # Get blog info
            blog_info_ref = post.get("blogInfo", "")
            blog_info = {}
            if blog_info_ref.startswith("s"):
                blog_info = assignments.get(blog_info_ref, {})

            author = sanitize(blog_info.get("blogNickName", "Unknown"))
            blog_name = sanitize(blog_info.get("blogName", ""))

            # Get other properties
            publish_time = post.get("publishTime", "")
            blog_page_url = post.get("blogPageUrl", "")
            post_id = post.get("postId", "") or post.get("id", "")

            # If no blogPageUrl, try to construct from other data
            if not blog_page_url:
                skipped_no_url += 1
                # Try to use blog_name and postId/publishTime as fallback
                fallback_id = post_id or publish_time
                if blog_name and fallback_id:
                    blog_page_url = f"https://{blog_name}.lofter.com/post/{fallback_id}"

            if not blog_name and blog_page_url:
                blog_name = extract_blog_name(blog_page_url)
            if not blog_name:
                skipped_no_blog += 1
                continue

            # Parse date
            try:
                if publish_time and publish_time.isdigit():
                    published_at = datetime.fromtimestamp(
                        int(publish_time) / 1000
                    ).isoformat()
                else:
                    published_at = datetime.now().isoformat()
            except Exception:
                published_at = datetime.now().isoformat()

            # Get tags
            tag_list_str = post.get("tagList", "")
            tags = []
            if tag_list_str:
                # Parse tag list from JavaScript array format
                tag_matches = re.findall(r'"([^"]+)"', tag_list_str)
                tags = tag_matches if tag_matches else []
            tags = [sanitize(tag) for tag in tags if tag]
            # Filter by actual tags (in addition to title filter above)
            if exclude_any_tag(tags, exclude_tags):
                continue

            # Get hot/bookmark count
            hot = post.get("hot", "0")
            try:
                kudos = int(hot) if hot.isdigit() else 0
            except Exception:
                kudos = 0

            # Get digest as summary
            digest = post.get("digest", "")
            summary = sanitize(clean_html(digest)) if digest else "暂无简介"

            # Extract post ID from URL and combine with blog_name
            post_id_match = re.search(r"/post/([^/?#]+)", blog_page_url or "")
            post_id = (
                post_id_match.group(1) if post_id_match else (post_id or publish_time)
            )
            # Store as blogName:postId so we can reconstruct the URL later
            novel_id = f"{blog_name}:{post_id}" if blog_name else post_id
            if not novel_id or novel_id in seen_ids:
                continue
            seen_ids.add(novel_id)

            novel = Novel(
                id=novel_id,
                source=NovelSource.LOFTER,
                title=title if title else "无标题",
                author=author,
                author_url=f"https://{blog_name}.lofter.com" if blog_name else "",
                summary=summary[:500],
                tags=tags[:10],
                word_count=None,
                chapter_count=1,
                kudos=kudos,
                hits=None,
                rating=None,
                published_at=published_at,
                updated_at=published_at,
                source_url=blog_page_url,
                cover_image=None,  # Lofter posts may have images in content
                is_complete=True,
            )

            novels.append(novel)
            parsed_count += 1

        logger.info(
            "Lofter DWR stats: %s parsed, %s skipped (no blog), %s had no URL (used fallback)",
            parsed_count,
            skipped_no_blog,
            skipped_no_url,
        )
        logger.info("Lofter: parsed %s novels from response", len(novels))
        return novels

    except Exception as e:
        logger.exception("Lofter parse error")
        return []


def clean_html(html: str) -> str:
    """Remove HTML tags from string."""
    clean = re.sub(r"<[^>]+>", "", html)
    clean = clean.replace("&nbsp;", " ")
    clean = clean.replace("&lt;", "<")
    clean = clean.replace("&gt;", ">")
    clean = clean.replace("&amp;", "&")
    # Decode Unicode escapes
    clean = decode_unicode(clean)
    return clean.strip()


def strip_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def looks_like_post(data: dict) -> bool:
    if ("blogInfo" in data or "blogName" in data) and (
        "publishTime" in data or "blogPageUrl" in data or "title" in data
    ):
        return True
    return False
