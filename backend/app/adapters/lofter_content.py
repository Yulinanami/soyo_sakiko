"""
Lofter post content fetching.
"""

import logging
import re

from app.adapters.lofter_common import normalize_lofter_image_url, proxy_lofter_images
from app.adapters.utils import sanitize_html
from app.services.http_client import get_sync_client

logger = logging.getLogger(__name__)


def fetch_post_content(novel_id: str, cookie: str) -> str:
    """Fetch post content from Lofter."""
    try:
        # Construct post URL - novel_id format is blogName:postId
        if ":" in novel_id:
            parts = novel_id.split(":", 1)
            if len(parts) == 2:
                blog_name, post_id = parts
                # Standard post URL format
                post_url = f"https://{blog_name}.lofter.com/post/{post_id}"
            else:
                return "<p>无效的文章 ID 格式</p>"
        else:
            return f"<p>无效的文章 ID 格式: {novel_id}</p>"

        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        client = get_sync_client()
        response = client.get(post_url, headers=headers)

        if response.status_code != 200:
            return (
                f"<p>获取内容失败 (HTTP {response.status_code})</p>"
                f"<p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"
            )

        # Get text and handle encoding issues (remove surrogates)
        html = response.text.encode("utf-8", errors="surrogatepass").decode(
            "utf-8", errors="replace"
        )

        # Prefer DOM-based extraction for stability
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            container = (
                soup.select_one("div.postwrapper .content")
                or soup.select_one("div#postwrapper .content")
                or soup.select_one("div.post .content")
            )
            if container:
                content = str(container)
                content = proxy_lofter_images(content)
                return sanitize_html(content)
        except ImportError:
            pass

        # Try to find the post content with Lofter-specific patterns
        content_parts = []

        # Pattern 1: Extract images from bigimgsrc attribute (Lofter's image viewer)
        big_imgs = re.findall(r'bigimgsrc=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for img_url in big_imgs:
            img_url = normalize_lofter_image_url(img_url)
            content_parts.append(f'<img src="{img_url}" style="max-width:100%;"/>')

        # Pattern 2: Extract text from div.text
        text_matches = re.findall(
            r'<div[^>]*class="text"[^>]*>(.*?)</div>',
            html,
            re.DOTALL | re.IGNORECASE,
        )
        for text_content in text_matches:
            cleaned = re.sub(r"<[^>]+>", "", text_content).strip()
            if cleaned:
                if "<p" in text_content:
                    content_parts.append(text_content)
                else:
                    content_parts.append(f"<p>{text_content}</p>")

        # Pattern 3: Fallback - div.content
        if not content_parts:
            content_match = re.search(
                r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                html,
                re.DOTALL | re.IGNORECASE,
            )
            if content_match:
                content_parts.append(content_match.group(1))

        # Pattern 4: Fallback - any img with imglf in src
        if not content_parts:
            imgs = re.findall(
                r'<img[^>]+src=["\']([^"\']*(?:imglf|lf127)[^"\']*)["\'][^>]*>',
                html,
                re.IGNORECASE,
            )
            for img in imgs:
                content_parts.append(f'<img src="{img}" style="max-width:100%;"/>')

        if content_parts:
            content = "\n".join(content_parts)
            # Replace Lofter image URLs with proxy URLs
            content = proxy_lofter_images(content)
            return sanitize_html(content)

        # Fallback: provide link to view on Lofter
        return sanitize_html(
            f"<p>无法解析文章内容</p><p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"
        )

    except Exception as e:
        logger.exception("Lofter fetch error")
        return sanitize_html(f"<p>获取内容失败: {e}</p>")
