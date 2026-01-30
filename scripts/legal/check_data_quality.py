#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查法律文书数据表中的空值和数据质量问题
PostgreSQL 版本
"""

import psycopg2
import sys

# 数据库连接配置 - 从 docker-compose.yml 读取
# 容器内使用 db 作为 host，宿主机使用 localhost
DB_CONFIG = {
    'host': 'db',  # 容器内使用 db，宿主机使用 localhost
    'port': 5432,
    'user': 'admin',
    'password': 'Huaiye@2020**',
    'database': 'asset_catalog'
}


def connect_db():
    """连接数据库"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        # 尝试使用 localhost
        try:
            DB_CONFIG['host'] = 'localhost'
            conn = psycopg2.connect(**DB_CONFIG)
            print("✅ 数据库连接成功 (localhost)")
            return conn
        except Exception as e2:
            print(f"❌ 重试连接失败: {e2}")
            sys.exit(1)


def print_table(headers, rows):
    """简单的表格打印"""
    # 计算列宽
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    # 打印表头
    header_line = " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))
    
    # 打印数据
    for row in rows:
        print(" | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def check_null_values(conn):
    """检查各列的空值数量"""
    cursor = conn.cursor()
    
    # 需要检查的列
    columns = [
        'title', 'case_type', 'case_cause', 'trial_procedure', 
        'region', 'judgment_year', 'judgment_result', 'court_name'
    ]
    
    print("\n" + "=" * 60)
    print("📊 各字段空值统计")
    print("=" * 60)
    
    results = []
    for col in columns:
        query = f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN "{col}" IS NULL OR "{col}" = '' THEN 1 ELSE 0 END) as null_count
            FROM legal_documents
        """
        try:
            cursor.execute(query)
            row = cursor.fetchone()
            total, null_count = row
            null_count = int(null_count) if null_count else 0
            percent = (null_count / total * 100) if total > 0 else 0
            results.append([col, total, null_count, f"{percent:.2f}%"])
        except Exception as e:
            results.append([col, "错误", str(e)[:30], "-"])
    
    print_table(['字段名', '总记录数', '空值数', '空值比例'], results)
    

def check_case_type_distribution(conn):
    """检查案件类型分布"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("📊 案件类型分布")
    print("=" * 60)
    
    query = """
        SELECT 
            COALESCE(case_type, '(空)') as case_type,
            COUNT(*) as count
        FROM legal_documents
        GROUP BY case_type
        ORDER BY count DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    results = [[row[0] if row[0] else '(空)', row[1]] for row in rows]
    print_table(['案件类型', '数量'], results)


def check_judgment_result_distribution(conn):
    """检查判决结果分布"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("📊 判决结果分布（前20种）")
    print("=" * 60)
    
    query = """
        SELECT 
            COALESCE(judgment_result, '(空)') as judgment_result,
            COUNT(*) as count
        FROM legal_documents
        GROUP BY judgment_result
        ORDER BY count DESC
        LIMIT 20
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        val = row[0] if row[0] else '(空)'
        if len(val) > 50:
            val = val[:50] + '...'
        results.append([val, row[1]])
    print_table(['判决结果', '数量'], results)


def check_sample_empty_results(conn, limit=10):
    """查看部分结果为空的记录"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print(f"📊 判决结果为空的记录示例（前{limit}条）")
    print("=" * 60)
    
    query = f"""
        SELECT doc_id, title, case_type, case_cause, judgment_year
        FROM legal_documents
        WHERE judgment_result IS NULL OR judgment_result = ''
        LIMIT {limit}
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        doc_id, title, case_type, case_cause, year = row
        title = (title[:30] + '...') if title and len(title) > 30 else (title or '')
        case_cause = (case_cause[:20] + '...') if case_cause and len(case_cause) > 20 else (case_cause or '')
        results.append([doc_id, title, case_type or '', case_cause, year or ''])
    
    print_table(['ID', '标题', '类型', '案由', '年份'], results)


def check_case_type_empty(conn, limit=10):
    """查看类型为空的记录"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print(f"📊 案件类型为空的记录示例（前{limit}条）")
    print("=" * 60)
    
    query = f"""
        SELECT doc_id, title, case_cause, region, judgment_year
        FROM legal_documents
        WHERE case_type IS NULL OR case_type = ''
        LIMIT {limit}
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if not rows:
        print("没有找到案件类型为空的记录")
        return
    
    results = []
    for row in rows:
        doc_id, title, case_cause, region, year = row
        title = (title[:30] + '...') if title and len(title) > 30 else (title or '')
        case_cause = (case_cause[:20] + '...') if case_cause and len(case_cause) > 20 else (case_cause or '')
        results.append([doc_id, title, case_cause, region or '', year or ''])
    
    print_table(['ID', '标题', '案由', '地域', '年份'], results)


def main():
    print("=" * 60)
    print("🔍 法律文书数据质量检查工具 (PostgreSQL)")
    print("=" * 60)
    
    conn = connect_db()
    
    try:
        check_null_values(conn)
        check_case_type_distribution(conn)
        check_judgment_result_distribution(conn)
        check_sample_empty_results(conn)
        check_case_type_empty(conn)
        
        print("\n" + "=" * 60)
        print("✅ 数据检查完成")
        print("=" * 60)
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
