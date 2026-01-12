"""
应急安全业务数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AlarmAssetBase(BaseModel):
    """告警资产基础模型"""
    asset_id: int
    filename: str
    filepath: str
    alarm_name: str
    alarm_time: datetime
    dev_code: Optional[str] = None
    analysis: Optional[str] = None


class AlarmAssetDetail(AlarmAssetBase):
    """告警资产详情模型"""
    filesize: int
    thumbnail_url: str
    download_url: str


class SearchRequest(BaseModel):
    """搜索请求模型"""
    alarm_types: Optional[List[str]] = Field(None, description="告警类型列表")
    dev_code: Optional[str] = Field(None, description="设备编码")
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    keyword: Optional[str] = Field(None, description="关键词（搜索分析结果）")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class SearchResponse(BaseModel):
    """搜索响应模型"""
    total: int
    page: int
    page_size: int
    data: List[AlarmAssetDetail]


class AlarmTypeResponse(BaseModel):
    """告警类型响应"""
    types: List[str]
