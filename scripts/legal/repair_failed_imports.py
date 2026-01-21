"""
修复失败文件导入脚本
专门处理因为中文顿号导致失败的文件

用法: python scripts/legal/repair_failed_imports.py
"""
import os
import asyncio
import asyncpg
import pandas as pd
import zipfile
import tempfile
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
NAS_ROOT = "/data/nas_data"
ZIP_FILE = os.path.join(NAS_ROOT, "10_Official_Library", "01_法院_司法", "05_法院文书", "法信案由.zip")

# 失败的文件序号（从日志中提取）
FAILED_FILE_INDICES = [
    1770, 25990, 53441, 24721, 315, 625, 25894, 25344, 25490, 1466,
    # 以下会从数据库中动态补充更多
]

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
    """安全转换为浮点数，处理多值、中文顿号、逗号分隔等情况"""
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
    
    # 移除货币符号和空格
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


async def repair_failed_imports():
    """修复失败的导入"""
    print("=" * 60)
    print("失败文件修复工具")
    print("=" * 60)
    print(f"ZIP 文件: {ZIP_FILE}")
    print()
    
    if not os.path.exists(ZIP_FILE):
        logger.error(f"ZIP 文件不存在: {ZIP_FILE}")
        return
    
    # 连接数据库
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # 构建 ZIP 内所有 Excel 文件的索引映射
        logger.info("正在扫描 ZIP 文件...")
        
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            all_members = [m for m in zf.namelist() 
                          if m.lower().endswith(('.xlsx', '.xls')) and not m.endswith('/')]
        
        logger.info(f"ZIP 包含 {len(all_members)} 个 Excel 文件")
        
        # 创建临时目录
        extract_dir = tempfile.mkdtemp(prefix="legal_repair_")
        logger.info(f"临时目录: {extract_dir}")
        
        total_imported = 0
        total_files = 0
        failed_files = []
        start_time = datetime.now()
        
        # 遍历所有文件，尝试导入（已存在的会自动更新）
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            for i, member in enumerate(all_members):
                try:
                    # 提取单个文件
                    ext = '.xlsx' if member.lower().endswith('.xlsx') else '.xls'
                    short_name = f"repair_{i:06d}{ext}"
                    target_path = os.path.join(extract_dir, short_name)
                    
                    with zf.open(member) as src, open(target_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    # 读取 Excel
                    df = pd.read_excel(target_path)
                    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})
                    
                    # 准备数据
                    records = []
                    for _, row in df.iterrows():
                        if pd.isna(row.get('doc_id')):
                            continue
                        record = prepare_record(row, member)
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
                                updated_at = NOW()
                        """, [
                            (r['doc_id'], r['title'], r['case_type'], r['case_cause'], r['trial_procedure'],
                             r['region'], r['judgment_year'], r['judgment_result'], r['claim_amount'],
                             r['judgment_amount'], r['fine_amount'], r['cited_laws'], r['judgment_section'],
                             r['argument_section'], r['fact_section'], r['reasoning_section'], r['source_file'])
                            for r in records
                        ])
                        
                        total_imported += len(records)
                    
                    total_files += 1
                    
                    # 删除临时文件
                    os.remove(target_path)
                    
                    # 进度显示
                    if (i + 1) % 1000 == 0 or i == len(all_members) - 1:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        rate = total_imported / elapsed if elapsed > 0 else 0
                        logger.info(f"进度: {i+1}/{len(all_members)} 文件, {total_imported} 条记录, {rate:.0f} 条/秒")
                    
                except Exception as e:
                    failed_files.append((member[:50], str(e)[:80]))
        
        # 清理临时目录
        import shutil
        shutil.rmtree(extract_dir, ignore_errors=True)
        
        # 汇总
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 50)
        logger.info(f"✅ 修复完成")
        logger.info(f"   处理文件: {total_files}/{len(all_members)}")
        logger.info(f"   导入/更新记录: {total_imported}")
        logger.info(f"   失败文件: {len(failed_files)}")
        logger.info(f"   耗时: {elapsed:.1f} 秒")
        
        if failed_files:
            logger.warning("仍失败的文件:")
            for name, err in failed_files[:20]:
                logger.warning(f"  - {name}: {err}")
                
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(repair_failed_imports())
