"""图片转发入口"""

import logging
import hashlib
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from cachetools import LRUCache
from app.services.http_client import get_async_client, get_no_proxy_async_client
from app.adapters.playwright_helpers import DEFAULT_UA

router = APIRouter()
logger = logging.getLogger(__name__)

image_cache: LRUCache = LRUCache(maxsize=50)

_SOURCE_CONFIG = {
    "pixiv": {
        "domains": ["pximg.net"],
        "referer": "https://www.pixiv.net/",
        "use_proxy": True,
    },
    "lofter": {
        "domains": [
            "lf127.net",
            "126.net",
            "lofter.com",
            "imglf",
            "nos.netease.com",
            "nosdn.127.net",
            "netease.com",
        ],
        "referer": "https://www.lofter.com/",
        "use_proxy": False,
    },
    "bilibili": {
        "domains": ["hdslb.com", "bilibili.com"],
        "referer": "https://www.bilibili.com/",
        "use_proxy": False,
    },
}


async def _proxy_image(url: str, source: str) -> Response:
    """通用图片代理：校验域名 → 查缓存 → 请求 → 存缓存 → 返回"""
    cfg = _SOURCE_CONFIG[source]

    # 补全协议
    if url and url.startswith("//"):
        url = f"https:{url}"

    # 域名白名单校验
    if not url or not any(d in url for d in cfg["domains"]):
        raise HTTPException(status_code=400, detail=f"Invalid {source} image URL")

    # 缓存命中
    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in image_cache:
        cached = image_cache[cache_key]
        return Response(
            content=cached["content"],
            media_type=cached["content_type"],
            headers={"Cache-Control": "public, max-age=86400"},
        )

    # 请求图片
    try:
        client = get_async_client() if cfg["use_proxy"] else get_no_proxy_async_client()
        response = await client.get(
            url,
            headers={
                "Referer": cfg["referer"],
                "User-Agent": DEFAULT_UA,
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            },
        )

        if response.status_code != 200:
            logger.warning(
                "%s image error: %s for %s", source, response.status_code, url
            )
            raise HTTPException(status_code=404, detail="Image not found")

        content = response.content
        content_type = response.headers.get("content-type", "image/jpeg")

        image_cache[cache_key] = {
            "content": content,
            "content_type": content_type,
        }

        return Response(
            content=content,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except httpx.TimeoutException:
        logger.warning("%s image timeout: %s", source, url)
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except HTTPException:
        raise
    except Exception:
        logger.exception("%s image error", source)
        raise HTTPException(status_code=500, detail="图片获取失败")


@router.get("/pixiv")
async def proxy_pixiv_image(url: str):
    """获取 Pixiv 图片"""
    return await _proxy_image(url, "pixiv")


@router.get("/lofter")
async def proxy_lofter_image(url: str):
    """获取 Lofter 图片"""
    return await _proxy_image(url, "lofter")


@router.get("/bilibili")
async def proxy_bilibili_image(url: str):
    """获取 Bilibili 图片"""
    return await _proxy_image(url, "bilibili")
