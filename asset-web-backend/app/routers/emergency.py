"""
应急安全API路由
"""
from fastapi import APIRouter
from app.models.emergency import (
    SearchRequest, SearchResponse, AlarmAssetDetail, AlarmTypeResponse
)
from app.services.emergency_service import emergency_service

router = APIRouter(prefix="/api/emergency", tags=["应急安全"])


@router.post("/search", response_model=SearchResponse)
async def search_alarms(req: SearchRequest):
    """
    搜索告警资产
    """
    total, data = await emergency_service.search_alarms(req)
    
    # 为每个结果添加URL
    results = []
    for item in data:
        results.append(AlarmAssetDetail(
            **item,
            thumbnail_url=f"/api/thumbnail/{item['asset_id']}",
            download_url=f"/api/download/{item['asset_id']}"
        ))
    
    return SearchResponse(
        total=total,
        page=req.page,
        page_size=req.page_size,
        data=results
    )


@router.get("/alarm-types", response_model=AlarmTypeResponse)
async def get_alarm_types():
    """
    获取所有告警类型
    """
    types = await emergency_service.get_alarm_types()
    return AlarmTypeResponse(types=types)
