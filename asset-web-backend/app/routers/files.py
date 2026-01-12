"""
文件相关API路由（缩略图、下载）
"""
import os
import io
import zipfile
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from app.services.file_service import file_service

router = APIRouter(prefix="/api", tags=["文件"])


class BatchDownloadRequest(BaseModel):
    """批量下载请求"""
    asset_ids: List[int]


@router.get("/thumbnail/{asset_id}")
async def get_thumbnail(asset_id: int):
    """
    获取资产缩略图
    """
    try:
        # 获取原始文件路径
        source_path = await file_service.get_asset_filepath(asset_id)

        # 生成缩略图
        thumbnail_path = file_service.generate_thumbnail(source_path, asset_id)

        return FileResponse(
            thumbnail_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"}
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Asset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{asset_id}")
async def download_file(asset_id: int):
    """
    下载资产文件
    """
    try:
        filepath = await file_service.get_asset_filepath(asset_id)

        if not filepath or not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")

        filename = os.path.basename(filepath)

        return FileResponse(
            filepath,
            media_type="application/octet-stream",
            filename=filename
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Asset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download/batch")
async def batch_download(req: BatchDownloadRequest):
    """
    批量下载资产文件（打包成ZIP）
    """
    if not req.asset_ids:
        raise HTTPException(status_code=400, detail="No assets selected")

    if len(req.asset_ids) > 100:
        raise HTTPException(status_code=400, detail="最多同时下载100个文件")

    # 创建内存中的ZIP文件
    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            added_files = set()

            for asset_id in req.asset_ids:
                try:
                    filepath = await file_service.get_asset_filepath(asset_id)

                    if filepath and os.path.exists(filepath):
                        filename = os.path.basename(filepath)

                        # 处理同名文件
                        original_name = filename
                        counter = 1
                        while filename in added_files:
                            name, ext = os.path.splitext(original_name)
                            filename = f"{name}_{counter}{ext}"
                            counter += 1

                        added_files.add(filename)
                        zf.write(filepath, filename)

                except Exception:
                    # 跳过无法访问的文件
                    continue

        if not added_files:
            raise HTTPException(status_code=404, detail="没有可下载的文件")

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"assets_{timestamp}.zip"

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
