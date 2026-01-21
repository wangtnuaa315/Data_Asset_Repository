"""
法律文书导入脚本 - 从 new_uploads 处理 Excel 文件

工作流程：
1. 扫描 00_Work_Area/new_uploads/ 目录中的 Excel 文件
2. 解析并导入数据到 legal_documents 表
3. 移动已处理的文件到 10_Official_Library--01_法院_司法/法院文书/

用法:
    python scripts/legal/import_legal_documents.py
    python scripts/legal/import_legal_documents.py --dry-run  # 预览模式
"""
import os
import sys
import asyncio
import asyncpg
import pandas as pd
import shutil
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
import argparse
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

# 目录配置
NEW_UPLOADS_DIR = os.path.join(NAS_ROOT, "00_Work_Area", "new_uploads")
TARGET_DIR = os.path.join(NAS_ROOT, "10_Official_Library", "01_法院_司法", "05_法院文书")

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 列名映射（Excel 列名 -> 数据库字段）
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


async def import_legal_documents(dry_run=False):
    """
    从 new_uploads 导入法律文书
    支持 Excel 文件（.xlsx, .xls）和 ZIP 压缩包
    """
    # 确保目录存在
    if not os.path.exists(NEW_UPLOADS_DIR):
        logger.warning(f"上传目录不存在: {NEW_UPLOADS_DIR}")
        logger.info(f"请先创建目录并上传文件")
        return
    
    # 确保目标目录存在
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # 获取所有 Excel 文件
    excel_files = list(Path(NEW_UPLOADS_DIR).glob("*.xlsx")) + \
                  list(Path(NEW_UPLOADS_DIR).glob("*.xls"))
    
    # 获取所有 ZIP 文件
    zip_files = list(Path(NEW_UPLOADS_DIR).glob("*.zip"))
    
    if not excel_files and not zip_files:
        logger.info(f"未找到 Excel 或 ZIP 文件: {NEW_UPLOADS_DIR}")
        return
    
    logger.info(f"找到 {len(excel_files)} 个 Excel 文件, {len(zip_files)} 个 ZIP 文件")
    
    if dry_run:
        logger.info("=== 预览模式 ===")
        for f in excel_files[:5]:
            logger.info(f"  Excel: {f.name}")
        for f in zip_files[:5]:
            logger.info(f"  ZIP: {f.name}")
        if len(excel_files) + len(zip_files) > 10:
            logger.info(f"  ... 共 {len(excel_files) + len(zip_files)} 个文件")
        return
    
    # 处理 ZIP 文件 - 解压到临时目录（处理长文件名问题）
    temp_extracted = []
    for zip_file in zip_files:
        try:
            extract_dir = tempfile.mkdtemp(prefix="legal_import_")
            extracted_count = 0
            
            with zipfile.ZipFile(zip_file, 'r') as zf:
                for i, member in enumerate(zf.namelist()):
                    if member.endswith('/'):
                        continue  # 跳过目录
                    
                    if not (member.lower().endswith('.xlsx') or member.lower().endswith('.xls')):
                        continue  # 只处理 Excel 文件
                    
                    # 使用序号作为文件名，避免文件名过长
                    ext = '.xlsx' if member.lower().endswith('.xlsx') else '.xls'
                    short_name = f"doc_{i:06d}{ext}"
                    target_path = os.path.join(extract_dir, short_name)
                    
                    # 读取并写入
                    with zf.open(member) as src, open(target_path, 'wb') as dst:
                        dst.write(src.read())
                    extracted_count += 1
                    
                    # 显示进度
                    if extracted_count % 1000 == 0:
                        logger.info(f"解压进度: {extracted_count} 个文件...")
            
            # 收集解压出的 Excel 文件
            extracted_excel = list(Path(extract_dir).glob("*.xlsx")) + \
                              list(Path(extract_dir).glob("*.xls"))
            
            logger.info(f"从 {zip_file.name} 解压 {len(extracted_excel)} 个 Excel 文件")
            
            for ef in extracted_excel:
                excel_files.append(ef)
            
            temp_extracted.append((zip_file, extract_dir))
            
        except Exception as e:
            logger.error(f"解压失败 {zip_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info(f"总计待处理 {len(excel_files)} 个 Excel 文件")
    
    # 连接数据库
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        total_imported = 0
        total_files = 0
        failed_files = []
        start_time = datetime.now()
        
        for i, excel_file in enumerate(excel_files):
            try:
                # 读取 Excel
                df = pd.read_excel(excel_file)
                
                # 重命名列
                df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})
                
                # 准备数据
                records = []
                for _, row in df.iterrows():
                    if pd.isna(row.get('doc_id')):
                        continue
                    
                    record = prepare_record(row, excel_file.name)
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
                
                # 移动文件到目标目录
                target_path = os.path.join(TARGET_DIR, excel_file.name)
                shutil.move(str(excel_file), target_path)
                total_files += 1
                
                # 进度显示
                if (i + 1) % 100 == 0 or i == len(excel_files) - 1:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = total_imported / elapsed if elapsed > 0 else 0
                    logger.info(f"进度: {i+1}/{len(excel_files)} 文件, {total_imported} 条记录, {rate:.0f} 条/秒")
                
            except Exception as e:
                failed_files.append((excel_file.name, str(e)))
                logger.error(f"处理失败 {excel_file.name}: {e}")
        
        # 汇总
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 50)
        logger.info(f"✅ 导入完成")
        logger.info(f"   处理文件: {total_files}/{len(excel_files)}")
        logger.info(f"   导入记录: {total_imported}")
        logger.info(f"   失败文件: {len(failed_files)}")
        logger.info(f"   耗时: {elapsed:.1f} 秒")
        logger.info(f"   文件已移动到: {TARGET_DIR}")
        
        if failed_files:
            logger.warning("失败文件列表:")
            for name, err in failed_files[:10]:
                logger.warning(f"  - {name}: {err}")
        
        # 移动 ZIP 文件到目标目录并清理临时目录
        for zip_file, extract_dir in temp_extracted:
            try:
                target_zip = os.path.join(TARGET_DIR, zip_file.name)
                shutil.move(str(zip_file), target_zip)
                shutil.rmtree(extract_dir, ignore_errors=True)
                logger.info(f"ZIP 已归档: {zip_file.name}")
            except Exception as e:
                logger.error(f"移动 ZIP 失败 {zip_file.name}: {e}")
                
    finally:
        await conn.close()


def safe_float(value):
    """安全转换为浮点数，处理多值、逗号分隔等情况"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    # 转换为字符串处理
    s = str(value).strip()
    if not s:
        return None
    
    # 处理中文顿号分隔的多个值（取第一个）
    if '、' in s:
        s = s.split('、')[0].strip()
    
    # 处理逗号分隔的多个值（取第一个）
    if ',' in s:
        s = s.split(',')[0].strip()
    
    # 移除可能的货币符号和空格
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='导入法律文书 Excel 文件')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际导入')
    args = parser.parse_args()
    
    print("=" * 60)
    print("法律文书导入工具")
    print("=" * 60)
    print(f"上传目录: {NEW_UPLOADS_DIR}")
    print(f"归档目录: {TARGET_DIR}")
    print()
    
    asyncio.run(import_legal_documents(dry_run=args.dry_run))
