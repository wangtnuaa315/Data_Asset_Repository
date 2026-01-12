"""
文件服务 - 缩略图和下载
"""
import os
import io
from PIL import Image
from pathlib import Path
from app.config import get_settings
from app.database import db

settings = get_settings()


class FileService:
    """文件服务"""
    
    def __init__(self):
        # 确保缩略图缓存目录存在
        Path(settings.thumbnail_cache_path).mkdir(parents=True, exist_ok=True)
    
    async def get_asset_filepath(self, asset_id: int) -> str:
        """获取资产文件路径"""
        sql = "SELECT filepath FROM asset_catalog WHERE id = $1 AND status = 'ready'"
        result = await db.fetch_one(sql, asset_id)
        if not result:
            raise FileNotFoundError(f"Asset {asset_id} not found")
        return result['filepath']
    
    def generate_thumbnail(self, source_path: str, asset_id: int) -> str:
        """
        生成缩略图
        
        Returns:
            缩略图文件路径
        """
        thumbnail_path = os.path.join(
            settings.thumbnail_cache_path,
            f"{asset_id}.jpg"
        )
        
        # 如果缩略图已存在，直接返回
        if os.path.exists(thumbnail_path):
            return thumbnail_path
        
        # 生成缩略图
        try:
            with Image.open(source_path) as img:
                # 转换为RGB（如果是RGBA）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # 等比例缩放
                img.thumbnail((settings.thumbnail_size, settings.thumbnail_size), Image.Resampling.LANCZOS)
                
                # 保存
                img.save(thumbnail_path, 'JPEG', quality=85)
            
            return thumbnail_path
        except Exception as e:
            raise RuntimeError(f"Failed to generate thumbnail: {str(e)}")


# 全局服务实例
file_service = FileService()
