"""
精准修复失败文件 - 只处理未成功导入的文件
通过比对目录文件和数据库记录，找出失败文件并重新导入

用法: python scripts/legal/repair_failed_only.py
"""
import os
import asyncio
import asyncpg
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# 配置
DB_CONFIG = {
    'host': '192.168.2.170',
    'port': 5432,
    'user': 'admin',
    'password': 'Huaiye@2020**',
    'database': 'asset_catalog'
}
EXCEL_DIR = "/data/nas_data/10_Official_Library/01_法院_司法/05_法院文书"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 列名映射
COLUMN_MAPPING = {
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


def safe_float(value):
    """安全转换为浮点数，处理中文顿号、逗号等"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    s = str(value).strip()
    if not s:
        return None
    
    # 处理中文顿号分隔（主要问题！）
    if '、' in s:
        s = s.split('、')[0].strip()
    
    # 处理英文逗号分隔
    if ',' in s:
        s = s.split(',')[0].strip()
    
    # 移除货币符号
    s = s.replace('¥', '').replace('￥', '').replace(' ', '')
    
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def safe_int(value):
    """安全转换为整数"""
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def prepare_record(row, source_file):
    """准备单条记录"""
    return {
        'doc_id': str(row.get('doc_id', '')),
        'title': str(row.get('title', '')) if pd.notna(row.get('title')) else None,
        'case_type': str(row.get('case_type', '')) if pd.notna(row.get('case_type')) else None,
        'case_cause': str(row.get('case_cause', '')) if pd.notna(row.get('case_cause')) else None,
        'trial_procedure': str(row.get('trial_procedure', '')) if pd.notna(row.get('trial_procedure')) else None,
        'region': str(row.get('region', '')) if pd.notna(row.get('region')) else None,
        'judgment_year': safe_int(row.get('judgment_year')),
        'judgment_result': str(row.get('judgment_result', '')) if pd.notna(row.get('judgment_result')) else None,
        'claim_amount': safe_float(row.get('claim_amount')),
        'judgment_amount': safe_float(row.get('judgment_amount')),
        'fine_amount': safe_float(row.get('fine_amount')),
        'cited_laws': str(row.get('cited_laws', '')) if pd.notna(row.get('cited_laws')) else None,
        'judgment_section': str(row.get('judgment_section', '')) if pd.notna(row.get('judgment_section')) else None,
        'argument_section': str(row.get('argument_section', '')) if pd.notna(row.get('argument_section')) else None,
        'fact_section': str(row.get('fact_section', '')) if pd.notna(row.get('fact_section')) else None,
        'reasoning_section': str(row.get('reasoning_section', '')) if pd.notna(row.get('reasoning_section')) else None,
        'source_file': source_file
    }


async def repair_failed_only():
    """只修复失败的文件"""
    print("=" * 60)
    print("精准修复工具 - 只处理失败文件")
    print("=" * 60)
    
    # 连接数据库
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # 1. 获取目录中所有 Excel 文件
        logger.info("扫描目录中的 Excel 文件...")
        all_files = set()
        for f in Path(EXCEL_DIR).glob("*.xlsx"):
            all_files.add(f.name)
        for f in Path(EXCEL_DIR).glob("*.xls"):
            all_files.add(f.name)
        
        logger.info(f"目录中共 {len(all_files)} 个 Excel 文件")
        
        # 2. 获取数据库中已成功导入的 source_file
        logger.info("查询数据库已导入文件...")
        rows = await conn.fetch("SELECT DISTINCT source_file FROM legal_documents")
        imported_files = set(row['source_file'] for row in rows if row['source_file'])
        
        logger.info(f"数据库中有 {len(imported_files)} 个不同来源文件")
        
        # 3. 找出失败的文件
        failed_files = all_files - imported_files
        logger.info(f"待修复文件: {len(failed_files)} 个")
        
        if not failed_files:
            logger.info("没有需要修复的文件！")
            return
        
        # 4. 重新导入失败文件
        total_imported = 0
        still_failed = []
        start_time = datetime.now()
        
        for i, filename in enumerate(sorted(failed_files)):
            filepath = os.path.join(EXCEL_DIR, filename)
            
            try:
                # 读取 Excel
                df = pd.read_excel(filepath)
                df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})
                
                # 准备数据
                records = []
                for _, row in df.iterrows():
                    if pd.isna(row.get('doc_id')):
                        continue
                    record = prepare_record(row, filename)
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
                            claim_amount = EXCLUDED.claim_amount,
                            judgment_amount = EXCLUDED.judgment_amount,
                            fine_amount = EXCLUDED.fine_amount,
                            source_file = EXCLUDED.source_file,
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
                if (i + 1) % 100 == 0 or i == len(failed_files) - 1:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = total_imported / elapsed if elapsed > 0 else 0
                    logger.info(f"进度: {i+1}/{len(failed_files)} 文件, {total_imported} 条记录, {rate:.0f} 条/秒")
                
            except Exception as e:
                still_failed.append((filename, str(e)[:100]))
        
        # 汇总
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 50)
        logger.info(f"✅ 修复完成")
        logger.info(f"   处理文件: {len(failed_files) - len(still_failed)}/{len(failed_files)}")
        logger.info(f"   新增记录: {total_imported}")
        logger.info(f"   仍失败: {len(still_failed)}")
        logger.info(f"   耗时: {elapsed:.1f} 秒")
        
        if still_failed:
            logger.warning("仍失败的文件:")
            for name, err in still_failed[:20]:
                logger.warning(f"  - {name}: {err}")
                
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(repair_failed_only())
