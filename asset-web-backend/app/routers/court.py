"""
法院卷宗模块 - API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional
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


@router.get("/dossiers/{dossier_code}/preview")
async def preview_dossier(dossier_code: str):
    """
    预览卷宗文件
    
    支持 PDF 和图片格式
    """
    filepath = await court_service.get_dossier_filepath(dossier_code)
    if not filepath:
        raise HTTPException(status_code=404, detail="卷宗文件不存在")
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在于存储中")
    
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type is None:
        mime_type = "application/octet-stream"
    
    return FileResponse(
        path=filepath,
        media_type=mime_type,
        filename=os.path.basename(filepath)
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
