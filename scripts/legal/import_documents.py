"""
批量导入法律文书 Excel 文件到数据库
用法: python scripts/legal/import_documents.py <excel_dir>
"""
import os
import sys
import asyncio
import asyncpg
import pandas as pd
from pathlib import Path
from datetime import datetime

# 配置
DATABASE_URL = "postgresql://admin:admin123@localhost:5432/asset_catalog"
BATCH_SIZE = 500  # 每批插入数量


async def import_excel_files(excel_dir: str):
    """批量导入 Excel 文件"""
    excel_path = Path(excel_dir)
    
    if not excel_path.exists():
        print(f"❌ 目录不存在: {excel_dir}")
        return
    
    # 获取所有 Excel 文件
    excel_files = list(excel_path.glob("*.xlsx")) + list(excel_path.glob("*.xls"))
    print(f"找到 {len(excel_files)} 个 Excel 文件")
    
    if not excel_files:
        print("未找到 Excel 文件")
        return
    
    # 连接数据库
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        total_imported = 0
        total_errors = 0
        start_time = datetime.now()
        
        # 列名映射（Excel 列名 -> 数据库字段）
        column_mapping = {
            'id': 'doc_id',
            '标题': 'title',
            '案件类型': 'case_type',
            '案由': 'case_cause',
            '审理程序': 'trial_procedure',
            '地域': 'region',
            '裁判年份': 'judgment_year',
            '裁判结果': 'judgment_result',
            '诉请金额': 'claim_amount',
            '判决金额': 'judgment_amount',
            '罚金': 'fine_amount',
            '引用法条': 'cited_laws',
            '裁判结果段': 'judgment_section',
            '诉辩意见段': 'argument_section',
            '事实认定段': 'fact_section',
            '裁判理由段': 'reasoning_section'
        }
        
        for i, excel_file in enumerate(excel_files):
            try:
                # 读取 Excel
                df = pd.read_excel(excel_file)
                
                # 重命名列
                df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
                
                # 准备数据
                records = []
                for _, row in df.iterrows():
                    # 跳过没有 doc_id 的行
                    if pd.isna(row.get('doc_id')):
                        continue
                    
                    record = {
                        'doc_id': str(row.get('doc_id', '')),
                        'title': str(row.get('title', '')) if pd.notna(row.get('title')) else None,
                        'case_type': str(row.get('case_type', '')) if pd.notna(row.get('case_type')) else None,
                        'case_cause': str(row.get('case_cause', '')) if pd.notna(row.get('case_cause')) else None,
                        'trial_procedure': str(row.get('trial_procedure', '')) if pd.notna(row.get('trial_procedure')) else None,
                        'region': str(row.get('region', '')) if pd.notna(row.get('region')) else None,
                        'judgment_year': int(row.get('judgment_year')) if pd.notna(row.get('judgment_year')) else None,
                        'judgment_result': str(row.get('judgment_result', '')) if pd.notna(row.get('judgment_result')) else None,
                        'claim_amount': float(row.get('claim_amount')) if pd.notna(row.get('claim_amount')) else None,
                        'judgment_amount': float(row.get('judgment_amount')) if pd.notna(row.get('judgment_amount')) else None,
                        'fine_amount': float(row.get('fine_amount')) if pd.notna(row.get('fine_amount')) else None,
                        'cited_laws': str(row.get('cited_laws', '')) if pd.notna(row.get('cited_laws')) else None,
                        'judgment_section': str(row.get('judgment_section', '')) if pd.notna(row.get('judgment_section')) else None,
                        'argument_section': str(row.get('argument_section', '')) if pd.notna(row.get('argument_section')) else None,
                        'fact_section': str(row.get('fact_section', '')) if pd.notna(row.get('fact_section')) else None,
                        'reasoning_section': str(row.get('reasoning_section', '')) if pd.notna(row.get('reasoning_section')) else None,
                        'source_file': excel_file.name
                    }
                    records.append(record)
                
                # 批量插入
                if records:
                    await conn.executemany("""
                        INSERT INTO legal_documents 
                        (doc_id, title, case_type, case_cause, trial_procedure, region,
                         judgment_year, judgment_result, claim_amount, judgment_amount, fine_amount,
                         cited_laws, judgment_section, argument_section, fact_section, reasoning_section,
                         source_file)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                        ON CONFLICT (doc_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            case_type = EXCLUDED.case_type,
                            case_cause = EXCLUDED.case_cause,
                            updated_at = NOW()
                    """, [
                        (r['doc_id'], r['title'], r['case_type'], r['case_cause'], r['trial_procedure'],
                         r['region'], r['judgment_year'], r['judgment_result'], r['claim_amount'],
                         r['judgment_amount'], r['fine_amount'], r['cited_laws'], r['judgment_section'],
                         r['argument_section'], r['fact_section'], r['reasoning_section'], r['source_file'])
                        for r in records
                    ])
                    
                    total_imported += len(records)
                
                # 进度显示
                if (i + 1) % 100 == 0 or i == len(excel_files) - 1:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = total_imported / elapsed if elapsed > 0 else 0
                    print(f"进度: {i+1}/{len(excel_files)} 文件, {total_imported} 条记录, {rate:.0f} 条/秒")
                    
            except Exception as e:
                total_errors += 1
                print(f"❌ 处理文件失败 {excel_file.name}: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n{'='*50}")
        print(f"✅ 导入完成")
        print(f"   总文件数: {len(excel_files)}")
        print(f"   导入记录: {total_imported}")
        print(f"   错误数: {total_errors}")
        print(f"   耗时: {elapsed:.1f} 秒")
        print(f"   速度: {total_imported/elapsed:.0f} 条/秒")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python import_documents.py <excel_directory>")
        print("示例: python import_documents.py /data/legal_documents/")
        sys.exit(1)
    
    asyncio.run(import_excel_files(sys.argv[1]))
