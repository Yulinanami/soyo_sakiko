"""
Credential capture routes for Pixiv/Lofter.
"""

from fastapi import APIRouter, HTTPException

from app.services.credential_service import credential_manager
from app.config import settings

router = APIRouter()


def _serialize_state(source: str):
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


@router.post("/{source}/start")
async def start_credential_flow(source: str):
    if source not in ("lofter", "pixiv"):
        raise HTTPException(status_code=404, detail="Unsupported source")
    if source == "lofter":
        credential_manager.start_lofter()
    else:
        credential_manager.start_pixiv()
    return _serialize_state(source)


@router.get("/{source}/status")
async def credential_status(source: str):
    if source not in ("lofter", "pixiv"):
        raise HTTPException(status_code=404, detail="Unsupported source")
    return _serialize_state(source)


@router.delete("/{source}")
async def clear_credentials(source: str):
    if source not in ("lofter", "pixiv"):
        raise HTTPException(status_code=404, detail="Unsupported source")
    credential_manager.clear(source)
    return _serialize_state(source)
