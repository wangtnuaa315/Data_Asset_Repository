"""
数据库连接管理
"""
import asyncpg
from typing import Optional
from urllib.parse import urlparse, unquote
from app.config import get_settings

settings = get_settings()


def parse_database_url(url: str) -> dict:
    """解析数据库URL为连接参数"""
    parsed = urlparse(url)
    return {
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": parsed.path.lstrip("/"),
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
    }


class Database:
    """数据库连接池管理"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """创建连接池"""
        db_config = parse_database_url(settings.database_url)
        self.pool = await asyncpg.create_pool(
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
            host=db_config["host"],
            port=db_config["port"],
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def disconnect(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
    
    async def fetch_all(self, query: str, *args):
        """查询多行"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetch_one(self, query: str, *args):
        """查询单行"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute(self, query: str, *args):
        """执行SQL"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)


# 全局数据库实例
db = Database()
