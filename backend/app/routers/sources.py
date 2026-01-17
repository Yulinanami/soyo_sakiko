"""
Sources Router
"""

from fastapi import APIRouter
from app.schemas.novel import NovelSource
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("/status", response_model=ApiResponse[dict])
async def get_sources_status():
    """Get status of all data sources"""
    return ApiResponse(
        data={
            "sources": [
                {
                    "name": NovelSource.AO3,
                    "display_name": "Archive of Our Own",
                    "status": "online",
                    "requires_auth": False,
                },
                {
                    "name": NovelSource.PIXIV,
                    "display_name": "Pixiv",
                    "status": "offline",  # Until configured
                    "requires_auth": True,
                },
                {
                    "name": NovelSource.LOFTER,
                    "display_name": "Lofter",
                    "status": "offline",  # Until configured
                    "requires_auth": True,
                },
            ]
        }
    )
