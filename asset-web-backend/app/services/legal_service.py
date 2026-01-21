"""
法律文书模块 - 业务服务层
"""
from typing import Optional, List, Tuple
from app.database import db
from app.models.legal import (
    LegalDocumentListItem, LegalDocumentDetail,
    CauseTreeNode, CauseStatsItem
)


class LegalService:
    """法律文书服务"""
    
    async def search_documents(
        self,
        keyword: Optional[str] = None,
        case_type: Optional[str] = None,
        case_causes: Optional[List[str]] = None,
        trial_procedure: Optional[str] = None,
        region: Optional[str] = None,
        judgment_year_start: Optional[int] = None,
        judgment_year_end: Optional[int] = None,
        judgment_result: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[LegalDocumentListItem], int]:
        """
        检索法律文书
        返回: (文书列表, 总数)
        """
        conditions = []
        params = []
        param_idx = 1
        
        # 关键词搜索（标题和案由）
        if keyword:
            conditions.append(f"(title ILIKE ${param_idx} OR case_cause ILIKE ${param_idx + 1})")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            param_idx += 2
        
        # 案件类型
        if case_type:
            conditions.append(f"case_type = ${param_idx}")
            params.append(case_type)
            param_idx += 1
        
        # 案由列表（来自级联选择器）
        if case_causes and len(case_causes) > 0:
            placeholders = ", ".join([f"${param_idx + i}" for i in range(len(case_causes))])
            conditions.append(f"case_cause IN ({placeholders})")
            params.extend(case_causes)
            param_idx += len(case_causes)
        
        # 审理程序
        if trial_procedure:
            conditions.append(f"trial_procedure = ${param_idx}")
            params.append(trial_procedure)
            param_idx += 1
        
        # 地域
        if region:
            conditions.append(f"region = ${param_idx}")
            params.append(region)
            param_idx += 1
        
        # 裁判年份范围
        if judgment_year_start:
            conditions.append(f"judgment_year >= ${param_idx}")
            params.append(judgment_year_start)
            param_idx += 1
        
        if judgment_year_end:
            conditions.append(f"judgment_year <= ${param_idx}")
            params.append(judgment_year_end)
            param_idx += 1
        
        # 裁判结果
        if judgment_result:
            conditions.append(f"judgment_result = ${param_idx}")
            params.append(judgment_result)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM legal_documents WHERE {where_clause}"
        count_row = await db.fetch_one(count_sql, *params)
        total = count_row[0] if count_row else 0
        
        # 查询列表（不含长文本）
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT id, doc_id, title, case_type, case_cause, trial_procedure,
                   region, judgment_year, judgment_result, created_at
            FROM legal_documents
            WHERE {where_clause}
            ORDER BY judgment_year DESC NULLS LAST, id DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        rows = await db.fetch_all(list_sql, *params, page_size, offset)
        
        items = [
            LegalDocumentListItem(
                id=row['id'],
                doc_id=row['doc_id'],
                title=row['title'],
                case_type=row['case_type'],
                case_cause=row['case_cause'],
                trial_procedure=row['trial_procedure'],
                region=row['region'],
                judgment_year=row['judgment_year'],
                judgment_result=row['judgment_result'],
                created_at=row['created_at']
            )
            for row in rows
        ]
        
        return items, total
    
    async def get_document_detail(self, doc_id: str) -> Optional[LegalDocumentDetail]:
        """获取文书详情"""
        sql = """
            SELECT id, doc_id, title, case_type, case_cause, trial_procedure,
                   region, judgment_year, judgment_result,
                   claim_amount, judgment_amount, fine_amount,
                   cited_laws, judgment_section, argument_section,
                   fact_section, reasoning_section, source_file,
                   created_at, updated_at
            FROM legal_documents
            WHERE doc_id = $1
        """
        row = await db.fetch_one(sql, doc_id)
        
        if not row:
            return None
        
        return LegalDocumentDetail(
            id=row['id'],
            doc_id=row['doc_id'],
            title=row['title'],
            case_type=row['case_type'],
            case_cause=row['case_cause'],
            trial_procedure=row['trial_procedure'],
            region=row['region'],
            judgment_year=row['judgment_year'],
            judgment_result=row['judgment_result'],
            claim_amount=row['claim_amount'],
            judgment_amount=row['judgment_amount'],
            fine_amount=row['fine_amount'],
            cited_laws=row['cited_laws'],
            judgment_section=row['judgment_section'],
            argument_section=row['argument_section'],
            fact_section=row['fact_section'],
            reasoning_section=row['reasoning_section'],
            source_file=row['source_file'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    async def get_cause_tree(self, case_type: Optional[str] = None) -> List[CauseTreeNode]:
        """获取案由树形结构"""
        # 查询所有节点
        if case_type:
            sql = """
                SELECT id, cause_name, case_type, parent_id, level, full_path
                FROM legal_cause_tree
                WHERE case_type = $1
                ORDER BY sort_order, id
            """
            rows = await db.fetch_all(sql, case_type)
        else:
            sql = """
                SELECT id, cause_name, case_type, parent_id, level, full_path
                FROM legal_cause_tree
                ORDER BY sort_order, id
            """
            rows = await db.fetch_all(sql)
        
        # 构建树形结构
        nodes_map = {}
        root_nodes = []
        
        for row in rows:
            node = CauseTreeNode(
                id=row['id'],
                cause_name=row['cause_name'],
                case_type=row['case_type'],
                parent_id=row['parent_id'],
                level=row['level'],
                full_path=row['full_path'],
                children=[]
            )
            nodes_map[node.id] = node
        
        # 构建父子关系
        for node in nodes_map.values():
            if node.parent_id is None:
                root_nodes.append(node)
            elif node.parent_id in nodes_map:
                nodes_map[node.parent_id].children.append(node)
        
        return root_nodes
    
    async def get_descendant_causes(self, parent_id: int) -> List[str]:
        """获取某节点下所有子孙案由名称（用于级联选择后的查询）"""
        # 使用递归CTE获取所有子孙
        sql = """
            WITH RECURSIVE cause_tree AS (
                SELECT id, cause_name
                FROM legal_cause_tree
                WHERE id = $1
                
                UNION ALL
                
                SELECT c.id, c.cause_name
                FROM legal_cause_tree c
                INNER JOIN cause_tree ct ON c.parent_id = ct.id
            )
            SELECT cause_name FROM cause_tree
        """
        rows = await db.fetch_all(sql, parent_id)
        return [row['cause_name'] for row in rows]
    
    async def get_regions(self) -> List[str]:
        """获取地域列表"""
        sql = """
            SELECT region FROM v_legal_region_stats
            WHERE region IS NOT NULL
            ORDER BY doc_count DESC
            LIMIT 100
        """
        rows = await db.fetch_all(sql)
        return [row['region'] for row in rows]
    
    async def get_trial_procedures(self) -> List[str]:
        """获取审理程序列表"""
        sql = """
            SELECT DISTINCT trial_procedure
            FROM legal_documents
            WHERE trial_procedure IS NOT NULL
            ORDER BY trial_procedure
        """
        rows = await db.fetch_all(sql)
        return [row['trial_procedure'] for row in rows]
    
    async def get_judgment_results(self) -> List[str]:
        """获取裁判结果列表"""
        sql = """
            SELECT judgment_result FROM v_legal_result_stats
            WHERE judgment_result IS NOT NULL
            ORDER BY doc_count DESC
            LIMIT 50
        """
        rows = await db.fetch_all(sql)
        return [row['judgment_result'] for row in rows]
    
    async def get_judgment_years(self) -> Tuple[int, int]:
        """获取裁判年份范围"""
        sql = """
            SELECT MIN(judgment_year) as min_year, MAX(judgment_year) as max_year
            FROM legal_documents
            WHERE judgment_year IS NOT NULL
        """
        row = await db.fetch_one(sql)
        return (row['min_year'] or 2015, row['max_year'] or 2025)
    
    async def get_cause_stats(self, case_type: Optional[str] = None) -> List[CauseStatsItem]:
        """获取案由统计（从实际数据中）"""
        if case_type:
            sql = """
                SELECT case_type, case_cause, doc_count
                FROM v_legal_cause_stats
                WHERE case_type = $1
                ORDER BY doc_count DESC
                LIMIT 100
            """
            rows = await db.fetch_all(sql, case_type)
        else:
            sql = """
                SELECT case_type, case_cause, doc_count
                FROM v_legal_cause_stats
                ORDER BY doc_count DESC
                LIMIT 200
            """
            rows = await db.fetch_all(sql)
        
        return [
            CauseStatsItem(
                case_type=row['case_type'],
                case_cause=row['case_cause'],
                doc_count=row['doc_count']
            )
            for row in rows
        ]


# 服务实例
legal_service = LegalService()
