"""Lofter 内容获取"""

import logging
import re
from app.adapters.lofter_common import normalize_lofter_image_url, proxy_lofter_images
from app.adapters.utils import sanitize_html
from app.services.http_client import get_no_proxy_sync_client, get_no_proxy_async_client

logger = logging.getLogger(__name__)


def fetch_post_content(novel_id: str, cookie: str) -> str:
    """获取 Lofter 文章内容"""
    try:
        if ":" in novel_id:
            parts = novel_id.split(":", 1)
            if len(parts) == 2:
                blog_name, post_id = parts
                post_url = f"https://{blog_name}.lofter.com/post/{post_id}"
            else:
                return "<p>无效的文章 ID 格式</p>"
        else:
            return f"<p>无效的文章 ID 格式: {novel_id}</p>"

        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        client = get_no_proxy_sync_client()
        response = client.get(post_url, headers=headers)

        if response.status_code != 200:
            return (
                f"<p>获取内容失败 (HTTP {response.status_code})</p>"
                f"<p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"
            )

        html = response.text.encode("utf-8", errors="surrogatepass").decode(
            "utf-8", errors="replace"
        )

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

        content_parts = []

        big_imgs = re.findall(r'bigimgsrc=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for img_url in big_imgs:
            img_url = normalize_lofter_image_url(img_url)
            content_parts.append(f'<img src="{img_url}" style="max-width:100%;"/>')

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

        if not content_parts:
            content_match = re.search(
                r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                html,
                re.DOTALL | re.IGNORECASE,
            )
            if content_match:
                content_parts.append(content_match.group(1))

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
            content = proxy_lofter_images(content)
            return sanitize_html(content)

        return sanitize_html(
            f"<p>无法解析文章内容</p><p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"
        )

    except Exception as e:
        logger.exception("Lofter fetch error")
        return sanitize_html(f"<p>获取内容失败: {e}</p>")


async def fetch_post_content_async(novel_id: str, cookie: str) -> str:
    """异步获取 Lofter 文章内容"""
    try:
        if ":" in novel_id:
            parts = novel_id.split(":", 1)
            if len(parts) == 2:
                blog_name, post_id = parts
                post_url = f"https://{blog_name}.lofter.com/post/{post_id}"
            else:
                return "<p>无效的文章 ID 格式</p>"
        else:
            return f"<p>无效的文章 ID 格式: {novel_id}</p>"

        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        client = get_no_proxy_async_client()
        response = await client.get(post_url, headers=headers)

        if response.status_code != 200:
            return (
                f"<p>获取内容失败 (HTTP {response.status_code})</p>"
                f"<p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"
            )

        html = response.text.encode("utf-8", errors="surrogatepass").decode(
            "utf-8", errors="replace"
        )

        return _parse_lofter_html(html, post_url)

    except Exception as e:
        logger.exception("Lofter async fetch error")
        return sanitize_html(f"<p>获取内容失败: {e}</p>")


def _parse_lofter_html(html: str, post_url: str) -> str:
    """解析 Lofter HTML 内容（sync/async 共用）"""
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

    content_parts = []

    big_imgs = re.findall(r'bigimgsrc=["\']([^"\']+)["\']', html, re.IGNORECASE)
    for img_url in big_imgs:
        img_url = normalize_lofter_image_url(img_url)
        content_parts.append(f'<img src="{img_url}" style="max-width:100%;"/>')

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

    if not content_parts:
        content_match = re.search(
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            html,
            re.DOTALL | re.IGNORECASE,
        )
        if content_match:
            content_parts.append(content_match.group(1))

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
        content = proxy_lofter_images(content)
        return sanitize_html(content)

    return sanitize_html(
        f"<p>无法解析文章内容</p><p><a href='{post_url}' target='_blank'>点击在新窗口查看原文</a></p>"
    )
