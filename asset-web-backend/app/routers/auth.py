"""
auth.py

认证API路由 - 处理用户登录和登出
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services.auth_service import auth_service


router = APIRouter(prefix='/auth', tags=['认证'])


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    username: str
    role: str
    message: str


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str


@router.post('/login', response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录
    
    - **username**: 用户名 (admin 或 user)
    - **password**: 密码
    """
    # 验证凭据
    user = auth_service.authenticate(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='用户名或密码错误'
        )
    
    # 生成Token
    token = auth_service.create_token(user['username'], user['role'])
    
    return LoginResponse(
        token=token,
        username=user['username'],
        role=user['role'],
        message='登录成功'
    )


@router.post('/logout', response_model=MessageResponse)
async def logout():
    """
    用户登出
    
    前端需要清除本地存储的Token
    """
    return MessageResponse(message='登出成功')


@router.get('/me', response_model=dict)
async def get_current_user_info(
    current_user: dict = None  # 暂时不验证，在实际使用中应该添加Depends
):
    """
    获取当前用户信息（测试接口）
    """
    return {'message': '请在请求头中携带Token'}
