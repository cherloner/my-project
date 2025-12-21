from datetime import datetime, timedelta, timezone
from typing import Optional
import random
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from ..database import get_db
from ..models import User

router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 短信验证码存储（生产环境应使用Redis）
sms_codes = {}

security = HTTPBearer()


class PhoneLoginRequest(BaseModel):
    phone: str
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v or len(v) < 10:
            raise ValueError('手机号格式不正确')
        return v


class VerifyCodeRequest(BaseModel):
    phone: str
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str


class UserProfile(BaseModel):
    id: str
    phone: str
    nickname: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    language: str
    roles: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


def generate_sms_code() -> str:
    """生成6位数字验证码"""
    return str(random.randint(100000, 999999))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证凭证已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/send-code", summary="发送短信验证码")
async def send_sms_code(request: PhoneLoginRequest):
    """发送短信验证码"""
    # 生成验证码
    code = generate_sms_code()
    
    # 存储验证码（生产环境应使用Redis，设置过期时间）
    sms_codes[request.phone] = {
        "code": code,
        "created_at": datetime.now(timezone.utc),
        "attempts": 0
    }
    
    # TODO: 实际项目中需要集成短信服务商API
    # 这里模拟发送，实际返回验证码用于测试
    
    return {
        "message": "验证码已发送",
        "code": code,  # 测试环境返回验证码，生产环境应删除
        "expires_in": 300  # 5分钟过期
    }


@router.post("/login", response_model=TokenResponse, summary="手机号验证码登录")
async def phone_login(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    """手机号验证码登录"""
    # 验证验证码
    if request.phone not in sms_codes:
        raise HTTPException(status_code=400, detail="验证码已过期或未发送")
    
    code_data = sms_codes[request.phone]
    
    # 检查验证码是否正确
    if code_data["code"] != request.code:
        code_data["attempts"] += 1
        if code_data["attempts"] >= 5:
            del sms_codes[request.phone]  # 超过5次尝试，删除验证码
        raise HTTPException(status_code=400, detail="验证码错误")
    
    # 检查验证码是否过期（5分钟）
    if datetime.now(timezone.utc) - code_data["created_at"] > timedelta(minutes=5):
        del sms_codes[request.phone]
        raise HTTPException(status_code=400, detail="验证码已过期")
    
    # 验证成功后删除验证码
    del sms_codes[request.phone]
    
    # 查找或创建用户
    user = db.query(User).filter(User.phone == request.phone).first()
    
    if not user:
        # 新用户自动注册
        user = User(
            phone=request.phone,
            nickname=f"用户{request.phone[-4:]}",  # 默认昵称
            language="zh-CN",
            roles=["learner"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id)
    )


@router.get("/profile", response_model=UserProfile, summary="获取用户资料")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户资料"""
    return UserProfile.from_orm(current_user)


@router.put("/profile", response_model=UserProfile, summary="更新用户资料")
async def update_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    # 允许更新的字段
    allowed_fields = ["nickname", "avatar_url", "bio", "language"]
    
    for field, value in profile_data.items():
        if field in allowed_fields and hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return UserProfile.from_orm(current_user)


@router.post("/refresh", response_model=TokenResponse, summary="刷新访问令牌")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """刷新访问令牌"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(current_user.id)
    )