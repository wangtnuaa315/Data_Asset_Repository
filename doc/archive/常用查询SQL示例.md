# 数据资产管理系统 - 常用查询SQL示例

## 📋 概述

本文档提供研发人员接入数据资产管理系统时常用的SQL查询示例，包括应急安全和法院业务场景�?

---

## 🔥 应急安全业务查�?

### 1. 基础查询 - 按告警类型搜�?

```sql
-- 查询火点检测告警的所有图�?
SELECT 
    a.id,
    a.filename,
    a.filepath,
    e.alarm_name,
    e.alarm_time,
    e.dev_code,
    e.analysis
FROM asset_catalog a
JOIN emergency_alarm_assets e ON a.id = e.asset_id
WHERE e.alarm_name LIKE '%火点检�?'
  AND a.status = 'ready'
ORDER BY e.alarm_time DESC
LIMIT 20;
```

### 2. 时间范围查询

```sql
-- 查询2025年Q4的所有告�?
SELECT 
    a.filename,
    a.filepath,
    a.quarter,
    e.alarm_name,
    e.alarm_time,
    e.dev_code
FROM asset_catalog a
JOIN emergency_alarm_assets e ON a.id = e.asset_id
WHERE e.alarm_time >= '2025-10-01'
  AND e.alarm_time < '2026-01-01'
  AND a.status = 'ready'
ORDER BY e.alarm_time DESC;
```

### 3. 设备维度查询

```sql
-- 查询特定设备的所有告�?
SELECT 
    COUNT(*) as total_alarms,
    e.alarm_name,
    MIN(e.alarm_time) as first_alarm,
    MAX(e.alarm_time) as last_alarm
FROM emergency_alarm_assets e
JOIN asset_catalog a ON e.asset_id = a.id
WHERE e.dev_code = 'DEV001'
  AND a.status = 'ready'
GROUP BY e.alarm_name
ORDER BY total_alarms DESC;
```

### 4. 多重告警查询

```sql
-- 查询触发多种告警的文�?
SELECT 
    a.filename,
    a.filepath,
    COUNT(DISTINCT e.alarm_name) as alarm_count,
    STRING_AGG(DISTINCT e.alarm_name, ' + ' ORDER BY e.alarm_name) as alarm_types
FROM asset_catalog a
JOIN emergency_alarm_assets e ON a.id = e.asset_id
WHERE a.status = 'ready'
GROUP BY a.id, a.filename, a.filepath
Having COUNT(DISTINCT e.alarm_name) > 1
ORDER BY alarm_count DESC;
```

### 5. AI分析结果查询

```sql
-- 查询包含特定AI分析结果的告�?
SELECT 
    a.filename,
    e.alarm_name,
    e.alarm_time,
    e.analysis
FROM asset_catalog a
JOIN emergency_alarm_assets e ON a.id = e.asset_id
WHERE e.analysis LIKE '%火情%'
  AND a.status = 'ready'
ORDER BY e.alarm_time DESC
LIMIT 10;
```

### 6. 分类统计查询

```sql
-- 按告警类型统计数�?
SELECT 
    e.alarm_name,
    COUNT(*) as count,
    MIN(e.alarm_time) as earliest,
    MAX(e.alarm_time) as latest
FROM emergency_alarm_assets e
JOIN asset_catalog a ON e.asset_id = a.id
WHERE a.status = 'ready'
GROUP BY e.alarm_name
ORDER BY count DESC;
```

### 7. 完整信息查询（含JSONB扩展字段�?

```sql
-- 查询告警的完整信息（包括业务扩展数据�?
SELECT 
    a.filename,
    a.filepath,
    a.filesize,
    e.alarm_name,
    e.alarm_time,
    e.dev_code,
    e.analysis,
    e.business_data->>'channel_name' as channel_name,
    e.business_data->>'area_name' as area_name,
    e.business_data->>'process_user_name' as processor,
    e.business_data
FROM asset_catalog a
JOIN emergency_alarm_assets e ON a.id = e.asset_id
WHERE e.alarm_name = '火点检测报警事�?
  AND a.status = 'ready'
ORDER BY e.alarm_time DESC
LIMIT 10;
```

---

## ⚖️ 法院业务查询（示例结构）

### 假设的法院业务表结构

```sql
-- 未来创建的法院业务表（示例）
CREATE TABLE court_case_assets (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT NOT NULL REFERENCES asset_catalog(id) ON DELETE CASCADE,
    
    -- 核心业务字段
    case_number VARCHAR(64),           -- 案件编号
    case_type VARCHAR(32),             -- 案件类型：民�?刑事/行政
    court_name VARCHAR(128),           -- 法院名称
    case_date DATE,                    -- 案件日期
    parties TEXT,                      -- 当事�?
    judge_name VARCHAR(64),            -- 主审法官
    case_status VARCHAR(32),           -- 案件状�?
    
    -- 扩展业务数据
    case_data JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1. 法院基础查询

```sql
-- 查询民事案件的所有文�?
SELECT 
    a.filename,
    a.filepath,
    c.case_number,
    c.case_type,
    c.court_name,
    c.case_date,
    c.parties
FROM asset_catalog a
JOIN court_case_assets c ON a.id = c.asset_id
WHERE c.case_type = '民事诉讼'
  AND a.status = 'ready'
ORDER BY c.case_date DESC
LIMIT 20;
```

### 2. 法院时间范围查询

```sql
-- 查询2025年的所有案�?
SELECT 
    a.filename,
    c.case_number,
    c.case_type,
    c.court_name,
    c.case_date
FROM asset_catalog a
JOIN court_case_assets c ON a.id = c.asset_id
WHERE c.case_date >= '2025-01-01'
  AND c.case_date < '2026-01-01'
  AND a.status = 'ready'
ORDER BY c.case_date DESC;
```

### 3. 法院案件号查�?

```sql
-- 根据案件编号查询所有相关文�?
SELECT 
    a.filename,
    a.filepath,
    a.filesize,
    c.case_number,
    c.case_type,
    c.parties,
    c.judge_name
FROM asset_catalog a
JOIN court_case_assets c ON a.id = c.asset_id
WHERE c.case_number = '(2025)�?1民初12345�?
  AND a.status = 'ready';
```

### 4. 法院统计查询

```sql
-- 按案件类型统计文档数�?
SELECT 
    c.case_type,
    COUNT(*) as document_count,
    MIN(c.case_date) as earliest_case,
    MAX(c.case_date) as latest_case
FROM court_case_assets c
JOIN asset_catalog a ON c.asset_id = a.id
WHERE a.status = 'ready'
GROUP BY c.case_type
ORDER BY document_count DESC;
```

---

## 🔍 跨业务查�?

### 1. 查询所有业务线的资产总览

```sql
-- 统计各业务线的资产数�?
SELECT 
    industry,
    category,
    COUNT(*) as asset_count,
    SUM(filesize) as total_size_bytes,
    ROUND(SUM(filesize) / 1024.0 / 1024.0 / 1024.0, 2) as total_size_gb
FROM asset_catalog
WHERE status = 'ready'
GROUP BY industry, category
ORDER BY industry, category;
```

### 2. 按年份季度统�?

```sql
-- 按年份和季度统计资产分布
SELECT 
    industry,
    year,
    quarter,
    COUNT(*) as count
FROM asset_catalog
WHERE status = 'ready'
  AND year IS NOT NULL
GROUP BY industry, year, quarter
ORDER BY industry, year, quarter;
```

### 3. 文件类型统计

```sql
-- 按文件扩展名统计
SELECT 
    industry,
    file_ext,
    COUNT(*) as count,
    SUM(filesize) as total_bytes
FROM asset_catalog
WHERE status = 'ready'
GROUP BY industry, file_ext
ORDER BY industry, count DESC;
```

---

## 🚀 API开发查询示�?

### FastAPI/Flask 后端查询示例

```python
# Python代码示例 - 应急安全告警搜索API

from fastapi import FastAPI, Query
from typing import Optional
import psycopg2
from datetime import datetime

app = FastAPI()

@app.get("/api/alarms/search")
async def search_alarms(
    alarm_type: Optional[str] = None,
    dev_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = Query(20, le=100)
):
    """搜索告警资产"""
    
    conn = psycopg2.connect("dbname=asset_catalog user=admin password=xxx")
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 构建动态SQL
    sql = """
        SELECT 
            a.id as asset_id,
            a.filename,
            a.filepath,
            e.alarm_name,
            e.alarm_time,
            e.dev_code,
            e.analysis
        FROM asset_catalog a
        JOIN emergency_alarm_assets e ON a.id = e.asset_id
        WHERE a.status = 'ready'
    """
    params = []
    
    if alarm_type:
        sql += " AND e.alarm_name LIKE %s"
        params.append(f"%{alarm_type}%")
    
    if dev_code:
        sql += " AND e.dev_code = %s"
        params.append(dev_code)
    
    if start_date:
        sql += " AND e.alarm_time >= %s"
        params.append(start_date)
    
    if end_date:
        sql += " AND e.alarm_time <= %s"
        params.append(end_date)
    
    if keyword:
        sql += " AND (e.analysis LIKE %s OR a.filename LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    
    sql += " ORDER BY e.alarm_time DESC LIMIT %s"
    params.append(limit)
    
    cur.execute(sql, params)
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return {
        "total": len(results),
        "data": results
    }
```

---

## 📝 性能优化建议

### 1. 使用索引字段查询

```sql
-- �?好的查询（使用索引字段）
SELECT * FROM emergency_alarm_assets WHERE alarm_time > '2025-01-01';

-- �?避免全表扫描
SELECT * FROM emergency_alarm_assets WHERE analysis LIKE '%关键�?';
```

### 2. 使用EXPLAIN分析查询计划

```sql
-- 分析查询性能
EXPLAIN ANALYZE
SELECT a.filename, e.alarm_name
FROM asset_catalog a
JOIN emergency_alarm_assets e ON a.id = e.asset_id
WHERE e.alarm_time > '2025-01-01';
```

### 3. 分页查询

```sql
-- 分页查询（推荐）
SELECT * FROM emergency_alarm_assets
ORDER BY alarm_time DESC
LIMIT 20 OFFSET 0;  -- �?�?

LIMIT 20 OFFSET 20;  -- �?�?
```

---

## 🔗 相关文档

- [数据库设计文档](file:///C:/Users/wangt/.gemini/antigravity/brain/4124c23c-5604-46c7-b3f8-f4a23d197936/database_design.md)
- [init_database.sql](file:///c:/Users/wangt/Desktop/语义检索增强部�?192.168.2.170�?92.168.1.77�?init_database.sql)
- [应急安全完整流程报告](file:///C:/Users/wangt/.gemini/antigravity/brain/4124c23c-5604-46c7-b3f8-f4a23d197936/应急安全完整流程报�?md)

