"""
配置管理模块
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "资产检索系统API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 数据库配置
    database_url: str = "postgresql://admin:Huaiye@2020**@db:5432/asset_catalog"
    
    # 文件存储配置
    nas_base_path: str = "/data/nas_data"
    thumbnail_cache_path: str = "/tmp/thumbnails"
    thumbnail_size: int = 200
    
    # CORS配置
    cors_origins: list = ["http://192.168.2.170:8082", "http://localhost:8082"]
    
    # 分页配置
    default_page_size: int = 20
    max_page_size: int = 100
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
