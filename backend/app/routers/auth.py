"""登录相关路由"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, AuthResponse, User as UserSchema, UserLogin
from app.schemas.response import ApiResponse
from app.config import settings

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """核对密码是否一致"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """把密码转换成保存用的值"""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """生成登录用的码"""
    to_encode = data.copy()
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """检查并获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        raw_sub = payload.get("sub")
        if raw_sub is None:
            raise credentials_exception
        try:
            user_id = int(raw_sub)
        except (TypeError, ValueError):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=ApiResponse[AuthResponse])
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """注册账号"""
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.id})

    return ApiResponse(
        data=AuthResponse(
            access_token=access_token, user=UserSchema.model_validate(user)
        )
    )


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    """登录账号"""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id})

    return ApiResponse(
        data=AuthResponse(
            access_token=access_token, user=UserSchema.model_validate(user)
        )
    )


@router.get("/me", response_model=ApiResponse[UserSchema])
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return ApiResponse(data=UserSchema.model_validate(current_user))
