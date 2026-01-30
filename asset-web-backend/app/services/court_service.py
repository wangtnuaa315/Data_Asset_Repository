"""
法院卷宗模块 - 业务服务层
使用 asyncpg 异步数据库连接
"""
from typing import Optional, List, Tuple
from app.database import db
from app.models.court import (
    CaseDetail, DossierDetail, DossierTreeNode,
    get_category_name, DOSSIER_CATEGORY_MAP
)


class CourtService:
    """法院卷宗服务"""
    
    async def search_cases(
        self,
        ah: Optional[str] = None,
        ay_ms: Optional[str] = None,
        ajlx_mc: Optional[str] = None,
        trial_stage: Optional[int] = None,
        cbr_mc: Optional[str] = None,
        region: Optional[str] = None,
        dossier_categories: Optional[List[int]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[CaseDetail], int]:
        """
        检索案件列表
        返回: (案件列表, 总数)
        """
        # 构建WHERE子句
        conditions = ["isdel = 0"]
        params = []
        param_idx = 1
        
        if ah:
            conditions.append(f"ah ILIKE ${param_idx}")
            params.append(f"%{ah}%")
            param_idx += 1
        
        if ay_ms:
            conditions.append(f"ay_ms = ${param_idx}")
            params.append(ay_ms)
            param_idx += 1
        
        if ajlx_mc:
            conditions.append(f"ajlx_mc = ${param_idx}")
            params.append(ajlx_mc)
            param_idx += 1
        
        if trial_stage:
            conditions.append(f"trial_stage = ${param_idx}")
            params.append(trial_stage)
            param_idx += 1
        
        if cbr_mc:
            conditions.append(f"cbr_mc ILIKE ${param_idx}")
            params.append(f"%{cbr_mc}%")
            param_idx += 1
        
        if region:
            conditions.append(f"fymc = ${param_idx}")
            params.append(region)
            param_idx += 1
        
        # 按卷宗分类筛选：查找包含指定分类卷宗的案件
        if dossier_categories:
            placeholders = ", ".join([f"${param_idx + i}" for i in range(len(dossier_categories))])
            conditions.append(f"""
                case_code IN (
                    SELECT DISTINCT case_code FROM court_dossiers 
                    WHERE isdel = 0 AND dossier_category IN ({placeholders})
                )
            """)
            params.extend(dossier_categories)
            param_idx += len(dossier_categories)
        
        if start_date:
            conditions.append(f"larq >= ${param_idx}")
            params.append(start_date)
            param_idx += 1
        
        if end_date:
            conditions.append(f"larq <= ${param_idx}")
            params.append(end_date)
            param_idx += 1
        
        if keyword:
            conditions.append(f"(aj_mc ILIKE ${param_idx} OR ah ILIKE ${param_idx + 1})")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            param_idx += 2
        
        where_clause = " AND ".join(conditions)
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM v_court_case_dossier_stats WHERE {where_clause}"
        count_row = await db.fetch_one(count_sql, *params)
        total = count_row[0] if count_row else 0
        
        # 查询列表
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT id, case_code, ah, aj_mc, fymc, ajlx_mc, ay_ms,
                   trial_stage, first_instance_ah, cbr_mc, larq, ktrq, bdje,
                   close_status, dossier_count, has_indictment, has_defense,
                   has_judgement, has_court_record, has_counterclaim,
                   created_at, updated_at
            FROM v_court_case_dossier_stats
            WHERE {where_clause}
            ORDER BY larq DESC, id DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        rows = await db.fetch_all(list_sql, *params, page_size, offset)
        
        cases = []
        for row in rows:
            cases.append(CaseDetail(
                id=row['id'],
                case_code=row['case_code'],
                ah=row['ah'],
                aj_mc=row['aj_mc'],
                fymc=row['fymc'],
                ajlx_mc=row['ajlx_mc'],
                ay_ms=row['ay_ms'],
                trial_stage=row['trial_stage'],
                first_instance_ah=row['first_instance_ah'],
                cbr_mc=row['cbr_mc'],
                larq=row['larq'],
                ktrq=row['ktrq'],
                bdje=row['bdje'],
                close_status=row['close_status'],
                dossier_count=row['dossier_count'] or 0,
                has_indictment=row['has_indictment'] or False,
                has_defense=row['has_defense'] or False,
                has_judgement=row['has_judgement'] or False,
                has_court_record=row['has_court_record'] or False,
                has_counterclaim=row['has_counterclaim'] or False,
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))
        
        return cases, total
    
    async def get_case_detail(self, case_code: str) -> Optional[CaseDetail]:
        """获取案件详情"""
        sql = """
            SELECT id, case_code, ah, aj_mc, fymc, ajlx_mc, ay_ms,
                   trial_stage, first_instance_ah, cbr_mc, larq, ktrq, bdje,
                   close_status, dossier_count, has_indictment, has_defense,
                   has_judgement, has_court_record, has_counterclaim,
                   created_at, updated_at
            FROM v_court_case_dossier_stats
            WHERE case_code = $1
        """
        row = await db.fetch_one(sql, case_code)
        
        if not row:
            return None
        
        return CaseDetail(
            id=row['id'],
            case_code=row['case_code'],
            ah=row['ah'],
            aj_mc=row['aj_mc'],
            fymc=row['fymc'],
            ajlx_mc=row['ajlx_mc'],
            ay_ms=row['ay_ms'],
            trial_stage=row['trial_stage'],
            first_instance_ah=row['first_instance_ah'],
            cbr_mc=row['cbr_mc'],
            larq=row['larq'],
            ktrq=row['ktrq'],
            bdje=row['bdje'],
            close_status=row['close_status'],
            dossier_count=row['dossier_count'] or 0,
            has_indictment=row['has_indictment'] or False,
            has_defense=row['has_defense'] or False,
            has_judgement=row['has_judgement'] or False,
            has_court_record=row['has_court_record'] or False,
            has_counterclaim=row['has_counterclaim'] or False,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    async def get_dossiers(self, case_code: str) -> List[DossierDetail]:
        """获取案件的卷宗列表"""
        sql = """
            SELECT cd.id, cd.dossier_code, cd.case_code, cd.original_name,
                   cd.original_suffix, cd.parent_dossier_code, cd.sfml,
                   cd.dossier_category, cd.classify, cd.summary, cd.priority,
                   cd.asset_id, cd.file_code, cd.created_at,
                   ac.filepath
            FROM court_dossiers cd
            LEFT JOIN asset_catalog ac ON cd.asset_id = ac.id
            WHERE cd.case_code = $1 AND cd.isdel = 0
            ORDER BY cd.priority, cd.id
        """
        rows = await db.fetch_all(sql, case_code)
        
        dossiers = []
        for row in rows:
            filepath = row['filepath']
            thumbnail_url = None
            download_url = None
            
            if filepath:
                download_url = f"/api/court/dossiers/{row['dossier_code']}/download"
                suffix = row['original_suffix']
                if suffix and suffix.lower() in ['jpg', 'jpeg', 'png', 'gif', 'pdf']:
                    thumbnail_url = f"/api/court/dossiers/{row['dossier_code']}/preview"
            
            dossiers.append(DossierDetail(
                id=row['id'],
                dossier_code=row['dossier_code'],
                case_code=row['case_code'],
                original_name=row['original_name'],
                original_suffix=row['original_suffix'],
                parent_dossier_code=row['parent_dossier_code'],
                sfml=row['sfml'],
                dossier_category=row['dossier_category'],
                classify=row['classify'],
                summary=row['summary'],
                priority=row['priority'],
                asset_id=row['asset_id'],
                file_code=row['file_code'],
                created_at=row['created_at'],
                thumbnail_url=thumbnail_url,
                download_url=download_url
            ))
        
        return dossiers
    
    def build_dossier_tree(self, dossiers: List[DossierDetail]) -> List[DossierTreeNode]:
        """构建卷宗树形结构"""
        children_map = {}
        root_items = []
        
        for d in dossiers:
            node = DossierTreeNode(
                dossier_code=d.dossier_code or str(d.id),
                name=d.original_name,
                is_folder=d.sfml == 1,
                category=d.dossier_category,
                category_name=get_category_name(d.dossier_category),
                download_url=d.download_url,
                children=[]
            )
            
            parent = d.parent_dossier_code
            if not parent or parent == 'root':
                root_items.append(node)
            else:
                if parent not in children_map:
                    children_map[parent] = []
                children_map[parent].append(node)
        
        def attach_children(node: DossierTreeNode):
            if node.dossier_code in children_map:
                node.children = children_map[node.dossier_code]
                for child in node.children:
                    attach_children(child)
        
        for root in root_items:
            attach_children(root)
        
        return root_items
    
    async def get_case_types(self) -> List[str]:
        """获取案件类型列表"""
        sql = "SELECT DISTINCT ajlx_mc FROM court_cases WHERE isdel = 0 AND ajlx_mc IS NOT NULL ORDER BY ajlx_mc"
        rows = await db.fetch_all(sql)
        return [row['ajlx_mc'] for row in rows]
    
    async def get_case_reasons(self) -> List[str]:
        """获取案由列表"""
        sql = "SELECT DISTINCT ay_ms FROM court_cases WHERE isdel = 0 AND ay_ms IS NOT NULL ORDER BY ay_ms"
        rows = await db.fetch_all(sql)
        return [row['ay_ms'] for row in rows]
    
    async def get_dossier_filepath(self, dossier_code: str) -> Optional[str]:
        """获取卷宗文件路径"""
        sql = """
            SELECT ac.filepath
            FROM court_dossiers cd
            JOIN asset_catalog ac ON cd.asset_id = ac.id
            WHERE cd.dossier_code = $1 AND cd.isdel = 0
        """
        row = await db.fetch_one(sql, dossier_code)
        return row['filepath'] if row else None
    
    async def search_dossiers_by_category(
        self,
        category_ids: Optional[List[int]] = None,
        case_code: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DossierDetail], int]:
        """
        按分类搜索卷宗
        
        Args:
            category_ids: 分类ID列表（多选）
            case_code: 案件编号
            keyword: 关键词（搜索文件名）
            page: 页码
            page_size: 每页数量
            
        Returns:
            (卷宗列表, 总数)
        """
        conditions = ["cd.isdel = 0"]
        params = []
        param_idx = 1
        
        if category_ids:
            placeholders = ', '.join([f'${i}' for i in range(param_idx, param_idx + len(category_ids))])
            conditions.append(f"cd.dossier_category IN ({placeholders})")
            params.extend(category_ids)
            param_idx += len(category_ids)
        
        if case_code:
            conditions.append(f"cd.case_code ILIKE ${param_idx}")
            params.append(f"%{case_code}%")
            param_idx += 1
        
        if keyword:
            conditions.append(f"cd.original_name ILIKE ${param_idx}")
            params.append(f"%{keyword}%")
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) FROM court_dossiers cd WHERE {where_clause}"
        count_row = await db.fetch_one(count_sql, *params)
        total = count_row[0] if count_row else 0
        
        # 查询列表
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT cd.id, cd.dossier_code, cd.case_code, cd.original_name,
                   cd.original_suffix, cd.parent_dossier_code, cd.sfml,
                   cd.dossier_category, cd.classify, cd.summary, cd.priority,
                   cd.asset_id, cd.file_code, cd.created_at,
                   ac.filepath
            FROM court_dossiers cd
            LEFT JOIN asset_catalog ac ON cd.asset_id = ac.id
            WHERE {where_clause}
            ORDER BY cd.dossier_category, cd.created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        rows = await db.fetch_all(list_sql, *params, page_size, offset)
        
        dossiers = []
        for row in rows:
            filepath = row['filepath']
            thumbnail_url = None
            download_url = None
            
            if filepath:
                download_url = f"/api/court/dossiers/{row['dossier_code']}/download"
                suffix = row['original_suffix']
                if suffix and suffix.lower() in ['jpg', 'jpeg', 'png', 'gif', 'pdf']:
                    thumbnail_url = f"/api/court/dossiers/{row['dossier_code']}/preview"
            
            dossiers.append(DossierDetail(
                id=row['id'],
                dossier_code=row['dossier_code'],
                case_code=row['case_code'],
                original_name=row['original_name'],
                original_suffix=row['original_suffix'],
                parent_dossier_code=row['parent_dossier_code'],
                sfml=row['sfml'],
                dossier_category=row['dossier_category'],
                classify=row['classify'],
                summary=row['summary'],
                priority=row['priority'],
                asset_id=row['asset_id'],
                file_code=row['file_code'],
                created_at=row['created_at'],
                thumbnail_url=thumbnail_url,
                download_url=download_url
            ))
        
        return dossiers, total
    
    async def get_category_stats(self) -> List[dict]:
        """获取各分类的卷宗统计"""
        sql = """
            SELECT dossier_category, classify, COUNT(*) as count
            FROM court_dossiers
            WHERE isdel = 0 AND dossier_category IS NOT NULL
            GROUP BY dossier_category, classify
            ORDER BY dossier_category
        """
        rows = await db.fetch_all(sql)
        return [{'id': row['dossier_category'], 'name': row['classify'], 'count': row['count']} for row in rows]
    
    async def get_case_dossier_files(self, case_code: str) -> List[dict]:
        """获取案件所有卷宗文件路径（用于打包下载）"""
        sql = """
            SELECT d.dossier_code, d.original_name, a.filepath
            FROM court_dossiers d
            LEFT JOIN asset_catalog a ON d.asset_id = a.id
            WHERE d.case_code = $1 AND d.isdel = 0 AND a.filepath IS NOT NULL
        """
        rows = await db.fetch_all(sql, case_code)
        return [{'dossier_code': row['dossier_code'], 'original_name': row['original_name'], 'filepath': row['filepath']} for row in rows]
    
    async def get_regions(self) -> List[str]:
        """获取所有区域列表（从数据库动态获取）"""
        sql = """
            SELECT DISTINCT fymc 
            FROM court_cases 
            WHERE fymc IS NOT NULL AND fymc != '' AND isdel = 0
            ORDER BY fymc
        """
        rows = await db.fetch_all(sql)
        return [row['fymc'] for row in rows]


# 服务实例
court_service = CourtService()

