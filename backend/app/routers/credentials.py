"""凭证相关路由"""

from fastapi import APIRouter, HTTPException

from app.services.credential_service import credential_manager
from app.config import settings
from app.schemas.response import ApiResponse

router = APIRouter()


def _serialize_state(source: str):
    """整理状态信息"""
    state = credential_manager.status(source)
    configured = False
    if source == "lofter":
        configured = bool(settings.LOFTER_COOKIE)
    if source == "pixiv":
        configured = bool(settings.PIXIV_REFRESH_TOKEN)
    return {
        "source": source,
        "state": state.state,
        "message": state.message,
        "updated_at": state.updated_at,
        "configured": configured,
    }


@router.post("/{source}/start", response_model=ApiResponse[dict])
async def start_credential_flow(source: str):
    """启动登录流程"""
    if source not in ("lofter", "pixiv"):
        raise HTTPException(status_code=404, detail="Unsupported source")
    if source == "lofter":
        credential_manager.start_lofter()
    else:
        credential_manager.start_pixiv()
    return ApiResponse(data=_serialize_state(source))


@router.get("/{source}/status", response_model=ApiResponse[dict])
async def credential_status(source: str):
    """获取登录状态"""
    if source not in ("lofter", "pixiv"):
        raise HTTPException(status_code=404, detail="Unsupported source")
    return ApiResponse(data=_serialize_state(source))


@router.delete("/{source}", response_model=ApiResponse[dict])
async def clear_credentials(source: str):
    """清除登录信息"""
    if source not in ("lofter", "pixiv"):
        raise HTTPException(status_code=404, detail="Unsupported source")
    credential_manager.clear(source)
    return ApiResponse(data=_serialize_state(source))
