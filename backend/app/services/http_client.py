"""共享访问工具"""

from typing import Optional

import httpx

_sync_client: Optional[httpx.Client] = None
_async_client: Optional[httpx.AsyncClient] = None
_no_proxy_async_client: Optional[httpx.AsyncClient] = None


def get_sync_client() -> httpx.Client:
    """获取常用访问工具"""
    global _sync_client
    if _sync_client is None:
        _sync_client = httpx.Client(timeout=30.0, follow_redirects=True)
    return _sync_client


def get_async_client() -> httpx.AsyncClient:
    """获取可同时使用的访问工具"""
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    return _async_client


def get_no_proxy_async_client() -> httpx.AsyncClient:
    """获取不走中转的访问工具"""
    global _no_proxy_async_client
    if _no_proxy_async_client is None:
        _no_proxy_async_client = httpx.AsyncClient(
            timeout=30.0, follow_redirects=True, proxy=None
        )
    return _no_proxy_async_client


def close_sync_client() -> None:
    """关闭常用访问工具"""
    global _sync_client
    if _sync_client is not None:
        _sync_client.close()
        _sync_client = None


async def close_async_client() -> None:
    """关闭可同时使用的访问工具"""
    global _async_client, _no_proxy_async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None
    if _no_proxy_async_client is not None:
        await _no_proxy_async_client.aclose()
        _no_proxy_async_client = None
