"""
应急安全业务服务层
"""
from typing import List, Tuple
from datetime import datetime
from app.database import db
from app.models.emergency import SearchRequest


class EmergencyService:
    """应急安全业务服务"""

    async def search_alarms(self, req: SearchRequest) -> Tuple[int, List[dict]]:
        """
        搜索告警资产

        Returns:
            (总数, 数据列表)
        """
        # 构建SQL查询
        where_clauses = ["a.status = 'ready'"]
        params = []
        param_idx = 1

        # 告警类型筛选
        if req.alarm_types:
            placeholders = ','.join(
                [f'${i}' for i in range(param_idx, param_idx + len(req.alarm_types))]
            )
            where_clauses.append(f"e.alarm_name IN ({placeholders})")
            params.extend(req.alarm_types)
            param_idx += len(req.alarm_types)

        # 设备编码筛选
        if req.dev_code:
            where_clauses.append(f"e.dev_code LIKE ${param_idx}")
            params.append(f"%{req.dev_code}%")
            param_idx += 1

        # 时间范围筛选 - 转换为datetime对象
        if req.start_date:
            where_clauses.append(f"e.alarm_time >= ${param_idx}")
            start_dt = datetime.strptime(f"{req.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S")
            params.append(start_dt)
            param_idx += 1

        if req.end_date:
            where_clauses.append(f"e.alarm_time <= ${param_idx}")
            end_dt = datetime.strptime(f"{req.end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
            params.append(end_dt)
            param_idx += 1

        # 关键词搜索 - 搜索告警名称、分析结果、文件名
        if req.keyword:
            keyword_pattern = f"%{req.keyword}%"
            where_clauses.append(
                f"(e.alarm_name ILIKE ${param_idx} OR "
                f"e.analysis ILIKE ${param_idx} OR "
                f"a.filename ILIKE ${param_idx})"
            )
            params.append(keyword_pattern)
            param_idx += 1
        
        where_sql = " AND ".join(where_clauses)
        
        # 查询总数
        count_sql = f"""
            SELECT COUNT(DISTINCT a.id)
            FROM asset_catalog a
            JOIN emergency_alarm_assets e ON a.id = e.asset_id
            WHERE {where_sql}
        """
        total_record = await db.fetch_one(count_sql, *params)
        total = total_record['count']
        
        # 查询数据
        offset = (req.page - 1) * req.page_size
        params.extend([req.page_size, offset])
        
        data_sql = f"""
            SELECT DISTINCT ON (a.id)
                a.id as asset_id,
                a.filename,
                a.filepath,
                a.filesize,
                e.alarm_name,
                e.alarm_time,
                e.dev_code,
                e.analysis
            FROM asset_catalog a
            JOIN emergency_alarm_assets e ON a.id = e.asset_id
            WHERE {where_sql}
            ORDER BY a.id, e.alarm_time DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        results = await db.fetch_all(data_sql, *params)
        
        return total, [dict(r) for r in results]
    
    async def get_alarm_types(self) -> List[str]:
        """获取所有告警类型"""
        sql = """
            SELECT DISTINCT alarm_name
            FROM emergency_alarm_assets
            WHERE alarm_name IS NOT NULL
            ORDER BY alarm_name
        """
        results = await db.fetch_all(sql)
        return [r['alarm_name'] for r in results]


# 全局服务实例
emergency_service = EmergencyService()
