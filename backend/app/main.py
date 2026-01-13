"""
SoyoSaki 同人文聚合器后端
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import novels, auth, sources
from app.config import settings

app = FastAPI(
    title="SoyoSaki API",
    description="素祥同人文聚合器 API",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(novels.router, prefix="/api/novels", tags=["novels"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])


@app.get("/")
async def root():
    return {"message": "SoyoSaki API is running", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
