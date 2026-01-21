"""
法律文书模块 - API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.models.legal import (
    LegalSearchRequest, LegalSearchResponse,
    LegalDocumentDetail, FilterOptionsResponse,
    CauseTreeResponse, CauseStatsResponse
)
from app.services.legal_service import legal_service

router = APIRouter(prefix="/api/legal", tags=["法律文书"])


@router.post("/documents/search", response_model=LegalSearchResponse)
async def search_documents(request: LegalSearchRequest):
    """
    检索法律文书
    
    支持条件：
    - keyword: 关键词（标题、案由模糊搜索）
    - case_type: 案件类型
    - case_causes: 案由列表
    - trial_procedure: 审理程序
    - region: 地域
    - judgment_year_start/end: 裁判年份范围
    - judgment_result: 裁判结果
    """
    items, total = await legal_service.search_documents(
        keyword=request.keyword,
        case_type=request.case_type,
        case_causes=request.case_causes,
        trial_procedure=request.trial_procedure,
        region=request.region,
        judgment_year_start=request.judgment_year_start,
        judgment_year_end=request.judgment_year_end,
        judgment_result=request.judgment_result,
        page=request.page,
        page_size=request.page_size
    )
    
    return LegalSearchResponse(
        items=items,
        total=total,
        page=request.page,
        page_size=request.page_size
    )


@router.get("/documents/{doc_id}", response_model=LegalDocumentDetail)
async def get_document_detail(doc_id: str):
    """获取法律文书详情"""
    detail = await legal_service.get_document_detail(doc_id)
    
    if not detail:
        raise HTTPException(status_code=404, detail="文书不存在")
    
    return detail


@router.get("/cause-tree", response_model=CauseTreeResponse)
async def get_cause_tree(case_type: Optional[str] = Query(None, description="案件类型筛选")):
    """
    获取案由树形结构
    
    用于前端级联选择器
    """
    tree = await legal_service.get_cause_tree(case_type)
    return CauseTreeResponse(items=tree)


@router.get("/cause-descendants/{parent_id}", response_model=FilterOptionsResponse)
async def get_cause_descendants(parent_id: int):
    """
    获取某节点下所有子孙案由名称
    
    当用户在级联选择器中选中一个节点后，
    调用此接口获取所有子孙案由用于查询
    """
    causes = await legal_service.get_descendant_causes(parent_id)
    return FilterOptionsResponse(items=causes)


@router.get("/cause-stats", response_model=CauseStatsResponse)
async def get_cause_stats(case_type: Optional[str] = Query(None)):
    """
    获取案由统计（从实际数据中统计）
    
    用于显示"数据中发现的案由"
    """
    stats = await legal_service.get_cause_stats(case_type)
    return CauseStatsResponse(items=stats)


@router.get("/regions", response_model=FilterOptionsResponse)
async def get_regions():
    """获取地域列表"""
    regions = await legal_service.get_regions()
    return FilterOptionsResponse(items=regions)


@router.get("/trial-procedures", response_model=FilterOptionsResponse)
async def get_trial_procedures():
    """获取审理程序列表"""
    procedures = await legal_service.get_trial_procedures()
    return FilterOptionsResponse(items=procedures)


@router.get("/judgment-results", response_model=FilterOptionsResponse)
async def get_judgment_results():
    """获取裁判结果列表"""
    results = await legal_service.get_judgment_results()
    return FilterOptionsResponse(items=results)


@router.get("/judgment-years")
async def get_judgment_years():
    """获取裁判年份范围"""
    min_year, max_year = await legal_service.get_judgment_years()
    return {"min_year": min_year, "max_year": max_year}


@router.get("/case-types", response_model=FilterOptionsResponse)
async def get_case_types():
    """获取案件类型列表"""
    return FilterOptionsResponse(items=["民事", "刑事", "行政", "赔偿"])
