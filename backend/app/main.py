"""SoyoSaki 同人文聚合器后端入口"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import novels, auth, proxy, credentials, user
from app.database import Base, engine
import app.models
from app.config import settings
from app.services.http_client import close_async_client, close_sync_client

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="SoyoSaki API", description="素祥同人文聚合器 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(novels.router, prefix="/api/novels", tags=["novels"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(proxy.router, prefix="/api/proxy", tags=["proxy"])
app.include_router(credentials.router, prefix="/api/credentials", tags=["credentials"])
app.include_router(user.router, prefix="/api/user", tags=["user"])


@app.on_event("startup")
def init_database() -> None:
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
async def shutdown_clients() -> None:
    """关闭网络连接"""
    close_sync_client()
    await close_async_client()


@app.get("/")
async def root():
    """返回服务提示"""
    return {"message": "SoyoSaki API is running", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """返回健康状态"""
    return {"status": "healthy"}
