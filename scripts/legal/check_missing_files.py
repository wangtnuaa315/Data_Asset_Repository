"""
检查未导入文件脚本
分析那些存在于目录但未出现在数据库中的文件

用法: python scripts/legal/check_missing_files.py
"""
import os
import asyncio
import asyncpg
import pandas as pd
from pathlib import Path

EXCEL_DIR = "/data/nas_data/10_Official_Library/01_法院_司法/05_法院文书"
DB_CONFIG = {
    'host': '192.168.2.170',
    'port': 5432,
    'user': 'admin',
    'password': 'Huaiye@2020**',
    'database': 'asset_catalog'
}


async def check_missing_files():
    print("=" * 60)
    print("检查未导入文件")
    print("=" * 60)
    
    # 1. 获取目录中所有 Excel 文件
    print("\n1. 扫描目录...")
    all_files = set()
    for f in Path(EXCEL_DIR).glob("*.xlsx"):
        all_files.add(f.name)
    for f in Path(EXCEL_DIR).glob("*.xls"):
        all_files.add(f.name)
    print(f"   目录中共 {len(all_files)} 个 Excel 文件")
    
    # 2. 获取数据库已导入的 source_file
    print("\n2. 查询数据库...")
    conn = await asyncpg.connect(**DB_CONFIG)
    rows = await conn.fetch("SELECT DISTINCT source_file FROM legal_documents")
    imported = set(row['source_file'] for row in rows if row['source_file'])
    await conn.close()
    print(f"   数据库中有 {len(imported)} 个已导入来源")
    
    # 3. 找出缺失的文件
    missing = all_files - imported
    print(f"\n3. 缺失文件: {len(missing)} 个")
    
    if not missing:
        print("\n✅ 所有文件都已成功导入！")
        return
    
    # 4. 分析缺失文件的原因
    print("\n4. 分析缺失文件原因（检查前 30 个）:")
    print("-" * 60)
    
    stats = {
        'no_id_column': 0,       # 没有 id 列
        'empty_file': 0,         # 文件为空或无数据行
        'all_id_null': 0,        # 有数据但 id 全为空
        'read_error': 0,         # 读取错误
        'unknown': 0             # 未知原因
    }
    
    sample_issues = []
    
    for i, fname in enumerate(sorted(missing)):
        fpath = os.path.join(EXCEL_DIR, fname)
        try:
            df = pd.read_excel(fpath)
            
            if len(df) == 0:
                reason = "文件为空"
                stats['empty_file'] += 1
            elif 'id' not in df.columns:
                reason = f"无id列，列名: {list(df.columns)[:3]}..."
                stats['no_id_column'] += 1
            else:
                valid_ids = df['id'].notna().sum()
                if valid_ids == 0:
                    reason = f"id全为空，共{len(df)}行"
                    stats['all_id_null'] += 1
                else:
                    reason = f"未知原因，行数={len(df)}, 有效id={valid_ids}"
                    stats['unknown'] += 1
            
            if i < 30:
                print(f"  {i+1:3}. {fname[:50]}: {reason}")
            sample_issues.append((fname, reason))
            
        except Exception as e:
            stats['read_error'] += 1
            if i < 30:
                print(f"  {i+1:3}. {fname[:50]}: 读取失败 - {str(e)[:50]}")
    
    # 5. 汇总统计
    print("\n" + "=" * 60)
    print("5. 原因统计:")
    print("-" * 60)
    print(f"   无 id 列:      {stats['no_id_column']}")
    print(f"   文件为空:      {stats['empty_file']}")
    print(f"   id 全为空:     {stats['all_id_null']}")
    print(f"   读取错误:      {stats['read_error']}")
    print(f"   未知原因:      {stats['unknown']}")
    print(f"   总计:          {sum(stats.values())}")
    
    # 6. 保存完整列表
    report_path = "/tmp/missing_files_report.txt"
    with open(report_path, 'w') as f:
        f.write("缺失文件报告\n")
        f.write("=" * 60 + "\n")
        for fname, reason in sample_issues:
            f.write(f"{fname}: {reason}\n")
    print(f"\n完整报告已保存到: {report_path}")


if __name__ == "__main__":
    asyncio.run(check_missing_files())
