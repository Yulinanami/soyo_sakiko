"""
SoyoSaki 同人文聚合器后端
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import novels, auth, sources, proxy, credentials, user
from app.database import Base, engine
import app.models  # noqa: F401
from app.config import settings

app = FastAPI(title="SoyoSaki API", description="素祥同人文聚合器 API", version="1.0.0")

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
app.include_router(proxy.router, prefix="/api/proxy", tags=["proxy"])
app.include_router(credentials.router, prefix="/api/credentials", tags=["credentials"])
app.include_router(user.router, prefix="/api/user", tags=["user"])


@app.on_event("startup")
def init_database() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {"message": "SoyoSaki API is running", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
