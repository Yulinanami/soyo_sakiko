"""图片转发入口"""

import logging
import httpx
import hashlib
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response


from app.services.http_client import get_async_client

router = APIRouter()
logger = logging.getLogger(__name__)

image_cache: dict = {}


@router.get("/pixiv")
async def proxy_pixiv_image(url: str):
    """获取 Pixiv 图片"""

    if not url or "pximg.net" not in url:
        raise HTTPException(status_code=400, detail="Invalid Pixiv image URL")

    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in image_cache:
        cached = image_cache[cache_key]
        return Response(
            content=cached["content"],
            media_type=cached["content_type"],
            headers={"Cache-Control": "public, max-age=86400"},
        )

    try:
        client = get_async_client()
        response = await client.get(
            url,
            headers={
                "Referer": "https://www.pixiv.net/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            },
        )

        if response.status_code != 200:
            logger.warning("Pixiv image error: %s for %s", response.status_code, url)
            raise HTTPException(status_code=404, detail="Image not found")

        content = response.content
        content_type = response.headers.get("content-type", "image/jpeg")

        if len(image_cache) < 100:
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
        logger.warning("Pixiv image timeout: %s", url)
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except Exception as e:
        logger.exception("Pixiv image error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lofter")
async def proxy_lofter_image(url: str):
    """获取 Lofter 图片"""

    lofter_domains = [
        "lf127.net",
        "126.net",
        "lofter.com",
        "imglf",
        "nos.netease.com",
        "nosdn.127.net",
        "netease.com",
    ]
    if url and url.startswith("//"):
        url = f"https:{url}"

    if not url or not any(domain in url for domain in lofter_domains):
        raise HTTPException(status_code=400, detail="Invalid Lofter image URL")

    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in image_cache:
        cached = image_cache[cache_key]
        return Response(
            content=cached["content"],
            media_type=cached["content_type"],
            headers={"Cache-Control": "public, max-age=86400"},
        )

    try:
        client = get_async_client()
        response = await client.get(
            url,
            headers={
                "Referer": "https://www.lofter.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            },
        )

        if response.status_code != 200:
            logger.warning("Lofter image error: %s for %s", response.status_code, url)
            raise HTTPException(status_code=404, detail="Image not found")

        content = response.content
        content_type = response.headers.get("content-type", "image/jpeg")

        if len(image_cache) < 100:
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
        logger.warning("Lofter image timeout: %s", url)
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except Exception as e:
        logger.exception("Lofter image error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bilibili")
async def proxy_bilibili_image(url: str):
    """获取 Bilibili 图片"""

    bilibili_domains = [
        "hdslb.com",
        "bilibili.com",
    ]
    if url and url.startswith("//"):
        url = f"https:{url}"

    if not url or not any(domain in url for domain in bilibili_domains):
        raise HTTPException(status_code=400, detail="Invalid Bilibili image URL")

    cache_key = hashlib.md5(url.encode()).hexdigest()
    if cache_key in image_cache:
        cached = image_cache[cache_key]
        return Response(
            content=cached["content"],
            media_type=cached["content_type"],
            headers={"Cache-Control": "public, max-age=86400"},
        )

    try:
        from app.services.http_client import get_no_proxy_async_client

        client = get_no_proxy_async_client()
        response = await client.get(
            url,
            headers={
                "Referer": "https://www.bilibili.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.warning("Bilibili image error: %s for %s", response.status_code, url)
            raise HTTPException(status_code=404, detail="Image not found")

        content = response.content
        content_type = response.headers.get("content-type", "image/jpeg")

        if len(image_cache) < 100:
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
        logger.warning("Bilibili image timeout: %s", url)
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except Exception as e:
        logger.exception("Bilibili image error")
        raise HTTPException(status_code=500, detail=str(e))
