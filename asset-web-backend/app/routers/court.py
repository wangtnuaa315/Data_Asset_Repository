"""
法院卷宗模块 - API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional, List
import os
import mimetypes

from app.models.court import (
    CaseSearchRequest, CaseSearchResponse,
    DossierListResponse, CaseDetail,
    DOSSIER_CATEGORY_MAP
)
from app.services.court_service import court_service

router = APIRouter(prefix="/api/court", tags=["法院卷宗"])


@router.post("/cases/search", response_model=CaseSearchResponse)
async def search_cases(request: CaseSearchRequest):
    """
    检索案件列表
    
    支持按案号、案由、案件类型、审判阶段、承办人、日期范围筛选
    """
    cases, total = await court_service.search_cases(
        ah=request.ah,
        ay_ms=request.ay_ms,
        ajlx_mc=request.ajlx_mc,
        trial_stage=request.trial_stage,
        cbr_mc=request.cbr_mc,
        region=request.region,
        dossier_categories=request.dossier_categories,
        start_date=request.start_date,
        end_date=request.end_date,
        keyword=request.keyword,
        page=request.page,
        page_size=request.page_size
    )
    
    return CaseSearchResponse(
        total=total,
        page=request.page,
        page_size=request.page_size,
        items=cases
    )


@router.get("/regions")
async def get_regions():
    """获取所有区域列表（从数据库动态获取）"""
    regions = await court_service.get_regions()
    return {"regions": regions}


@router.get("/cases/{case_code}/download-zip")
async def download_case_dossiers_zip(case_code: str):
    """打包下载案件所有卷宗（ZIP格式）"""
    import zipfile
    from io import BytesIO
    
    # 获取案件所有卷宗文件路径
    dossiers = await court_service.get_case_dossier_files(case_code)
    if not dossiers:
        raise HTTPException(status_code=404, detail="未找到该案件的卷宗文件")
    
    # 创建内存中的ZIP文件
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for dossier in dossiers:
            filepath = dossier.get('filepath')
            if filepath and os.path.exists(filepath):
                # 使用原始文件名作为ZIP内的文件名
                arcname = dossier.get('original_name', os.path.basename(filepath))
                zip_file.write(filepath, arcname)
    
    zip_buffer.seek(0)
    
    # 返回ZIP文件
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{case_code}.zip"'
        }
    )


@router.get("/cases/{case_code}", response_model=CaseDetail)
async def get_case_detail(case_code: str):
    """获取案件详情"""
    case = await court_service.get_case_detail(case_code)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    return case


@router.get("/cases/{case_code}/dossiers", response_model=DossierListResponse)
async def get_case_dossiers(case_code: str):
    """
    获取案件的卷宗列表
    
    返回平铺列表和树形结构两种格式
    """
    # 先验证案件存在
    case = await court_service.get_case_detail(case_code)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    
    dossiers = await court_service.get_dossiers(case_code)
    tree = court_service.build_dossier_tree(dossiers)
    
    return DossierListResponse(
        case_code=case_code,
        total=len(dossiers),
        items=dossiers,
        tree=tree
    )


@router.get("/dossiers/{dossier_code}/download")
async def download_dossier(dossier_code: str):
    """下载卷宗文件"""
    filepath = await court_service.get_dossier_filepath(dossier_code)
    if not filepath:
        raise HTTPException(status_code=404, detail="卷宗文件不存在")
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在于存储中")
    
    filename = os.path.basename(filepath)
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/case-types")
async def get_case_types():
    """获取案件类型列表（用于下拉筛选）"""
    types = await court_service.get_case_types()
    return {"items": types}


@router.get("/case-reasons")
async def get_case_reasons():
    """获取案由列表（用于下拉筛选）"""
    reasons = await court_service.get_case_reasons()
    return {"items": reasons}


@router.get("/dossier-categories")
async def get_dossier_categories():
    """获取卷宗分类列表"""
    return {"items": [
        {"id": k, "name": v} for k, v in DOSSIER_CATEGORY_MAP.items()
    ]}


@router.get("/dossiers/search")
async def search_dossiers(
    category_ids: Optional[str] = Query(None, description="分类ID，多个用逗号分隔"),
    case_code: Optional[str] = Query(None, description="案件编号"),
    keyword: Optional[str] = Query(None, description="关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    按分类搜索卷宗
    
    - category_ids: 分类ID，多个用逗号分隔，如 "1,3,6"
    - case_code: 案件编号（模糊搜索）
    - keyword: 文件名关键词
    """
    # 解析分类ID列表
    category_list = None
    if category_ids:
        try:
            category_list = [int(x.strip()) for x in category_ids.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="category_ids 格式错误")
    
    dossiers, total = await court_service.search_dossiers_by_category(
        category_ids=category_list,
        case_code=case_code,
        keyword=keyword,
        page=page,
        page_size=page_size
    )
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": dossiers
    }


@router.get("/dossiers/category-stats")
async def get_category_stats():
    """获取各分类的卷宗统计"""
    stats = await court_service.get_category_stats()
    return {"items": stats}

@router.get("/dossiers/{dossier_code}/preview")
async def preview_dossier(dossier_code: str):
    """在线预览卷宗文件（支持PDF、图片等）"""
    filepath = await court_service.get_dossier_filepath(dossier_code)
    if not filepath:
        raise HTTPException(status_code=404, detail="卷宗文件不存在")
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在于存储中")
    
    # 根据文件扩展名确定 MIME 类型
    ext = os.path.splitext(filepath)[1].lower()
    
    # 可以在浏览器内显示的类型
    previewable_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.txt': 'text/plain; charset=utf-8',
    }
    
    mime_type = previewable_types.get(ext)
    
    if mime_type:
        # 可预览类型：使用 Response 类手动返回，避免 FileResponse 自动设置 attachment
        from urllib.parse import quote
        from starlette.responses import Response
        
        filename = os.path.basename(filepath)
        encoded_filename = quote(filename, safe='')
        
        # 读取文件内容
        with open(filepath, 'rb') as f:
            content = f.read()
        
        return Response(
            content=content,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
            }
        )
    else:
        # 不可预览类型：触发下载
        from urllib.parse import quote
        filename = os.path.basename(filepath)
        encoded_filename = quote(filename, safe='')
        return FileResponse(
            path=filepath,
            media_type='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

