"""
Sources Router
"""

from fastapi import APIRouter
from app.schemas.novel import NovelSource

router = APIRouter()


@router.get("/status")
async def get_sources_status():
    """Get status of all data sources"""
    return {
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
