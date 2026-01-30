"""
法院卷宗模块 - Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# =====================================================
# 案件相关模型
# =====================================================

class CaseBase(BaseModel):
    """案件基础信息"""
    case_code: str = Field(..., description="案件唯一编号")
    ah: Optional[str] = Field(None, description="案号")
    aj_mc: Optional[str] = Field(None, description="案件名称")
    fymc: Optional[str] = Field(None, description="法院名称")
    ajlx_mc: Optional[str] = Field(None, description="案件类型描述")
    ay_ms: Optional[str] = Field(None, description="案由描述")
    trial_stage: Optional[int] = Field(None, description="审判阶段: 1=一审, 2=二审")
    first_instance_ah: Optional[str] = Field(None, description="一审案号")
    cbr_mc: Optional[str] = Field(None, description="承办人名称")
    larq: Optional[str] = Field(None, description="立案日期")
    ktrq: Optional[date] = Field(None, description="开庭日期")
    bdje: Optional[float] = Field(None, description="标的金额")
    close_status: Optional[int] = Field(0, description="结案状态")


class CaseDetail(CaseBase):
    """案件详情（含卷宗统计）"""
    id: int
    dossier_count: int = Field(0, description="卷宗数量")
    has_indictment: bool = Field(False, description="有起诉状")
    has_defense: bool = Field(False, description="有答辩状")
    has_judgement: bool = Field(False, description="有判决书")
    has_court_record: bool = Field(False, description="有庭审笔录")
    has_counterclaim: bool = Field(False, description="有反诉状")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# 卷宗相关模型
# =====================================================

class DossierBase(BaseModel):
    """卷宗基础信息"""
    dossier_code: Optional[str] = Field(None, description="卷宗唯一标识号")
    case_code: str = Field(..., description="案件唯一编号")
    original_name: str = Field(..., description="原始文件名")
    original_suffix: Optional[str] = Field(None, description="文件类型")
    parent_dossier_code: Optional[str] = Field(None, description="父节点")
    sfml: int = Field(0, description="是否目录: 0=否, 1=是")
    dossier_category: Optional[int] = Field(None, description="卷宗分类")
    classify: Optional[str] = Field(None, description="卷宗分类文本")


class DossierDetail(DossierBase):
    """卷宗详情"""
    id: int
    asset_id: Optional[int] = None
    file_code: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[int] = None
    # 文件访问URL
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DossierTreeNode(BaseModel):
    """卷宗树形节点"""
    dossier_code: str
    name: str
    is_folder: bool = False
    category: Optional[int] = None
    category_name: Optional[str] = None
    children: List["DossierTreeNode"] = []
    download_url: Optional[str] = None


# =====================================================
# 请求/响应模型
# =====================================================

class CaseSearchRequest(BaseModel):
    """案件检索请求"""
    ah: Optional[str] = Field(None, description="案号（模糊）")
    ay_id: Optional[str] = Field(None, description="案由编号")
    ay_ms: Optional[str] = Field(None, description="案由描述")
    ajlx_mc: Optional[str] = Field(None, description="案件类型")
    trial_stage: Optional[int] = Field(None, description="审判阶段")
    cbr_mc: Optional[str] = Field(None, description="承办人")
    region: Optional[str] = Field(None, description="区域（法院）")
    dossier_categories: Optional[List[int]] = Field(None, description="卷宗分类ID列表")
    start_date: Optional[str] = Field(None, description="立案开始日期")
    end_date: Optional[str] = Field(None, description="立案结束日期")
    keyword: Optional[str] = Field(None, description="关键词")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")



class CaseSearchResponse(BaseModel):
    """案件检索响应"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    items: List[CaseDetail] = Field(default_factory=list, description="案件列表")


class DossierListResponse(BaseModel):
    """卷宗列表响应"""
    case_code: str
    total: int
    items: List[DossierDetail]
    tree: List[DossierTreeNode] = Field(default_factory=list, description="树形结构")


# =====================================================
# 卷宗分类枚举
# =====================================================

DOSSIER_CATEGORY_MAP = {
    1: "起诉状",
    2: "答辩状",
    3: "证据",
    4: "其他文件",
    5: "原审判决书",
    6: "庭审笔录",
    7: "诉讼请求变更申请",
    8: "反诉状",
    9: "量刑建议书",
    10: "行政复议决定书",
    11: "立案审批表",
    12: "调解笔录",
    13: "调解协议",
    14: "送达回证",
    15: "上诉状",
    16: "听证笔录",
    17: "谈话笔录",
}


def get_category_name(category: Optional[int]) -> Optional[str]:
    """获取卷宗分类名称"""
    if category is None:
        return None
    return DOSSIER_CATEGORY_MAP.get(category)
