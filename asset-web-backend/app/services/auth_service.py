"""
auth_service.py

用户认证服务 - 处理登录验证和JWT Token管理
"""

import os
import yaml
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from functools import wraps
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# 加载配置
def load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config.yaml'
    )
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.config = load_config()
        self.auth_config = self.config.get('auth', {})
        self.secret_key = self.auth_config.get('secret_key', 'default-secret')
        self.expire_hours = self.auth_config.get('token_expire_hours', 24)
        
        # 用户配置
        self.users = {
            self.auth_config.get('admin', {}).get('username', 'admin'): {
                'password': self.auth_config.get('admin', {}).get('password', 'admin'),
                'role': 'admin'
            },
            self.auth_config.get('user', {}).get('username', 'user'): {
                'password': self.auth_config.get('user', {}).get('password', 'user123'),
                'role': 'user'
            }
        }
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        验证用户凭据
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            成功返回用户信息，失败返回None
        """
        user = self.users.get(username)
        if user and user['password'] == password:
            return {
                'username': username,
                'role': user['role']
            }
        return None
    
    def create_token(self, username: str, role: str) -> str:
        """
        创建JWT Token
        
        Args:
            username: 用户名
            role: 用户角色
            
        Returns:
            JWT Token字符串
        """
        payload = {
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.expire_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证JWT Token
        
        Args:
            token: JWT Token字符串
            
        Returns:
            成功返回payload，失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


# 创建单例
auth_service = AuthService()

# FastAPI安全依赖
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """获取当前登录用户"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token无效或已过期',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    
    return {
        'username': payload['username'],
        'role': payload['role']
    }


async def require_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """要求管理员权限"""
    if current_user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='需要管理员权限，请使用admin账号登录'
        )
    return current_user
