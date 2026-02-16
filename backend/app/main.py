"""SoyoSaki 同人文聚合器后端入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import novels, auth, proxy, credentials, user, download
from app.database import Base, engine
import app.models
from app.config import settings
from app.services.http_client import close_async_client, close_sync_client

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表，关闭时释放连接"""
    if settings.SECRET_KEY == "your-secret-key-change-in-production":
        logging.getLogger(__name__).warning(
            "⚠️  SECRET_KEY 使用了默认值，请在 .env 中设置安全的随机密钥！"
        )
    Base.metadata.create_all(bind=engine)
    yield
    close_sync_client()
    await close_async_client()


app = FastAPI(
    title="SoyoSaki API",
    description="素祥同人文聚合器 API",
    version="1.0.0",
    lifespan=lifespan,
)

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
app.include_router(download.router, prefix="/api/download", tags=["download"])


@app.get("/")
async def root():
    """返回服务提示"""
    return {"message": "SoyoSaki API is running", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """返回健康状态"""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获未处理的异常，返回统一格式"""
    logging.getLogger(__name__).exception(
        "Unhandled error: %s %s", request.method, request.url
    )
    return JSONResponse(
        status_code=500,
        content={"status": "error", "data": None, "error": "内部服务器错误"},
    )
