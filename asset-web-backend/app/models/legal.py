"""
法律文书模块 - Pydantic 数据模型
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# =====================================================
# 案由树相关模型
# =====================================================

class CauseTreeNode(BaseModel):
    """案由树节点"""
    id: int
    cause_name: str
    case_type: str
    parent_id: Optional[int] = None
    level: int
    full_path: Optional[str] = None
    children: List['CauseTreeNode'] = []

    class Config:
        from_attributes = True


class CauseTreeResponse(BaseModel):
    """案由树响应"""
    items: List[CauseTreeNode]


# =====================================================
# 法律文书相关模型
# =====================================================

class LegalDocumentBase(BaseModel):
    """法律文书基础字段"""
    doc_id: str
    title: str
    case_type: Optional[str] = None
    case_cause: Optional[str] = None
    trial_procedure: Optional[str] = None
    region: Optional[str] = None
    judgment_year: Optional[int] = None
    judgment_result: Optional[str] = None


class LegalDocumentListItem(LegalDocumentBase):
    """列表项（不含长文本）"""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LegalDocumentDetail(LegalDocumentBase):
    """详情（含长文本）"""
    id: int
    claim_amount: Optional[Decimal] = None
    judgment_amount: Optional[Decimal] = None
    fine_amount: Optional[Decimal] = None
    cited_laws: Optional[str] = None
    judgment_section: Optional[str] = None
    argument_section: Optional[str] = None
    fact_section: Optional[str] = None
    reasoning_section: Optional[str] = None
    source_file: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# 请求/响应模型
# =====================================================

class LegalSearchRequest(BaseModel):
    """检索请求"""
    keyword: Optional[str] = None              # 关键词（标题、案由模糊搜索）
    case_type: Optional[str] = None            # 案件类型
    case_causes: Optional[List[str]] = None    # 案由列表（级联选择的结果）
    trial_procedure: Optional[str] = None      # 审理程序
    region: Optional[str] = None               # 地域
    judgment_year_start: Optional[int] = None  # 裁判年份起
    judgment_year_end: Optional[int] = None    # 裁判年份止
    judgment_result: Optional[str] = None      # 裁判结果
    page: int = 1
    page_size: int = 20


class LegalSearchResponse(BaseModel):
    """检索响应"""
    items: List[LegalDocumentListItem]
    total: int
    page: int
    page_size: int


class FilterOptionsResponse(BaseModel):
    """筛选选项响应"""
    items: List[str]


class CauseStatsItem(BaseModel):
    """案由统计项"""
    case_type: str
    case_cause: str
    doc_count: int


class CauseStatsResponse(BaseModel):
    """案由统计响应"""
    items: List[CauseStatsItem]
