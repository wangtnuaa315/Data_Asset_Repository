#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
佛山法院卷宗导入脚本
import_foshan_dossiers.py

功能：
1. 扫描佛山法院目录下的案件ZIP文件和解压后的文件夹
2. 自动解压ZIP文件，过滤日志、Excel等非卷宗文件
3. 根据文件名自动识别分类
4. 导入到 court_cases 和 court_dossiers 表

佛山目录结构特点：
- 按日期组织: 2025-06-06/
- ZIP压缩包: （2025）粤0604民初6849号2025-05-29.zip
- 已解压文件夹: （2025）粤0604民初6849号2025-05-29/
- 使用全角括号（）

使用方式：
python3 scripts/court/import_foshan_dossiers.py
python3 scripts/court/import_foshan_dossiers.py --dry-run  # 预览模式
python3 scripts/court/import_foshan_dossiers.py --source /path/to/佛山目录
"""

import os
import re
import sys
import hashlib
import zipfile
import shutil
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import yaml
except ImportError as e:
    print(f"请安装依赖: pip install psycopg2-binary pyyaml")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/data_asset/logs/import_foshan.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =====================================================
# 分类配置
# =====================================================

CATEGORY_MAP = {
    1: "起诉状", 2: "答辩状", 3: "证据", 4: "其他文件",
    5: "原审判决书", 6: "庭审笔录", 7: "诉讼请求变更申请",
    8: "反诉状", 9: "量刑建议书", 10: "行政复议决定书",
    11: "立案审批表", 12: "调解笔录", 13: "调解协议",
    14: "送达回证", 15: "上诉状", 16: "听证笔录", 17: "谈话笔录",
}

# 文件名前缀编号 -> 分类ID
PREFIX_NUMBER_CATEGORY = {
    0: 1,   # 0_ 通常是起诉状
    1: 1,   # 1_ 起诉状
    2: 12,  # 2_ 调解笔录
}

# 文件名关键词 -> 分类ID
KEYWORD_CATEGORY_MAPPING = {
    '起诉状': 1, '诉状': 1, '民事起诉状': 1,
    '答辩状': 2, '答辩': 2,
    '证据目录': 3, '证据清单': 3, '证据': 3, '合同': 3, '借款': 3, '担保': 3,
    '凭证': 3, '账户查询': 3, '情况说明': 3, '保险单': 3, '保险': 3,
    '身份证': 3, '营业执照': 3, '授权委托书': 3, '委托书': 3,
    '诊断证明': 3, '病历': 3, '鉴定': 3, '工伤': 3,
    '不动产权证': 3, '产权证': 3, '社会保险': 3, '用工': 3, '劳动合同': 3,
    '庭审笔录': 6, '开庭笔录': 6, '审理笔录': 6,
    '听证笔录': 16, '听证': 16,
    '谈话笔录': 17, '谈话': 17,
    '调解笔录': 12, '调解协议': 13, '调解': 12,
    '判决书': 5, '民事判决': 5, '判决': 5,
    '立案审批': 11, '立案登记': 11, '立案': 11,
    '送达回证': 14, '送达': 14, '快递单': 14, '送达地址': 14, '快递面单': 14,
    '上诉状': 15,
    '反诉状': 8,
    '诉讼材料接收表': 3, '提交材料': 3, '材料清单': 3,
    '诚信诉讼承诺书': 3, '回避情形告知书': 3,
}

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff'}

# 需要排除的文件类型
EXCLUDED_EXTENSIONS = {'.log', '.out', '.xlsx', '.xls', '.rar', '.zip', '.7z', '.pyc', '.txt'}


class FoshanDossierImporter:
    """佛山法院卷宗导入器"""
    
    def __init__(self, config_path: str = '/opt/data_asset/config.yaml'):
        self.config = self.load_config(config_path)
        self.nas_base = self.config.get('nas', {}).get('base_path', '/data/nas_data')
        self.pg_config = self.config.get('postgresql', {})
        
        # 目录配置（与东台共用同一归档目录）
        self.archive_dir = os.path.join(self.nas_base, '10_Official_Library', '01_法院_司法', '03_电子卷宗库')
        
        # 模式控制
        self.dry_run = False
        self.no_move = False
        
        # 统计信息
        self.stats = {
            'cases_processed': 0,
            'files_imported': 0,
            'files_skipped': 0,
            'files_moved': 0,
            'zips_extracted': 0,
            'errors': 0,
        }
        self.report_items = []
    
    def load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return {
                'postgresql': {
                    'host': '192.168.2.170', 'port': 5432,
                    'user': 'admin', 'password': 'Huaiye@2020**',
                    'database': 'asset_catalog'
                },
                'nas': {'base_path': '/data/nas_data'}
            }
    
    def connect_db(self):
        return psycopg2.connect(
            host=self.pg_config.get('host', '192.168.2.170'),
            port=self.pg_config.get('port', 5432),
            user=self.pg_config.get('user', 'admin'),
            password=self.pg_config.get('password', 'Huaiye@2020**'),
            database=self.pg_config.get('database', 'asset_catalog'),
        )
    
    def get_file_md5(self, filepath: str) -> str:
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_case_code_from_zip(self, zip_name: str, parent_path: str = None) -> Optional[str]:
        """从ZIP/RAR文件名提取案号（保留日期作为案号一部分）
        
        佛山格式示例:
        - （2025）粤0604民初6849号2025-05-29.zip -> (2025)粤0604民初6849号_2025-05-29
        - (2025)粤0604民初6849号2025-05-29.zip -> (2025)粤0604民初6849号_2025-05-29
        """
        # 匹配全角括号格式: （2025）粤0604民初6849号2025-05-29
        pattern1 = r'（(\d{4})）粤(\d{4})(\w+)(\d+)号(\d{4}-\d{2}-\d{2})?'
        match = re.search(pattern1, zip_name)
        if match:
            year, court, case_type, num, date = match.groups()
            case_code = f"({year})粤{court}{case_type}{num}号"
            if date:
                case_code += "_" + date
            return case_code
        
        # 匹配半角括号格式: (2025)粤0604民初6849号2025-05-29
        pattern2 = r'\((\d{4})\)粤(\d{4})(\w+)(\d+)号(\d{4}-\d{2}-\d{2})?'
        match2 = re.search(pattern2, zip_name)
        if match2:
            year, court, case_type, num, date = match2.groups()
            case_code = f"({year})粤{court}{case_type}{num}号"
            if date:
                case_code += "_" + date
            return case_code
        
        # 匹配不带括号格式: 2025粤0604民初6849号2025-05-29
        pattern3 = r'(\d{4})粤(\d{4})(\w+)(\d+)号(\d{4}-\d{2}-\d{2})?'
        match3 = re.search(pattern3, zip_name)
        if match3:
            year, court, case_type, num, date = match3.groups()
            case_code = f"({year})粤{court}{case_type}{num}号"
            if date:
                case_code += "_" + date
            return case_code
        
        # 匹配纯数字文件名（如 6849.zip）
        base_name = os.path.splitext(zip_name)[0]
        pure_num_pattern = r'^(\d{3,5})$'
        match4 = re.match(pure_num_pattern, base_name)
        if match4:
            return match4.group(1)
        
        return None
    
    def extract_case_code_from_folder(self, folder_name: str, parent_path: str = None) -> Optional[str]:
        """从文件夹名提取案号（保留日期作为案号一部分）
        
        佛山格式示例:
        - （2025）粤0604民初6849号2025-05-29 -> (2025)粤0604民初6849号_2025-05-29
        """
        # 匹配全角括号格式
        pattern1 = r'（(\d{4})）粤(\d{4})(\w+)(\d+)号(\d{4}-\d{2}-\d{2})?'
        match = re.search(pattern1, folder_name)
        if match:
            year, court, case_type, num, date = match.groups()
            case_code = f"({year})粤{court}{case_type}{num}号"
            if date:
                case_code += "_" + date
            return case_code
        
        # 匹配半角括号格式
        pattern2 = r'\((\d{4})\)粤(\d{4})(\w+)(\d+)号(\d{4}-\d{2}-\d{2})?'
        match2 = re.search(pattern2, folder_name)
        if match2:
            year, court, case_type, num, date = match2.groups()
            case_code = f"({year})粤{court}{case_type}{num}号"
            if date:
                case_code += "_" + date
            return case_code
        
        # 匹配纯数字文件夹名
        pure_num_pattern = r'^(\d{3,5})$'
        match3 = re.match(pure_num_pattern, folder_name)
        if match3:
            return match3.group(1)
        
        return None
    
    def extract_case_code_from_folder_contents(self, folder_path: str) -> Optional[str]:
        """从文件夹内部文件名提取案号
        
        当文件夹名本身无法提取案号时，扫描内部文件名来提取
        例如：0812log/ 目录下有 （2025）粤0604民初2189号民事判决书.docx
        """
        if not os.path.exists(folder_path):
            return None
        
        # 只扫描第一层文件
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    # 尝试从文件名提取案号
                    case_code = self.extract_case_code_from_zip(item, folder_path)
                    if case_code:
                        logger.info(f"📂 从内部文件提取到案号: {case_code} (来自 {item})")
                        return case_code
                elif os.path.isdir(item_path):
                    # 尝试从子目录名提取案号
                    case_code = self.extract_case_code_from_folder(item, folder_path)
                    if case_code:
                        logger.info(f"📂 从子目录提取到案号: {case_code} (来自 {item})")
                        return case_code
        except Exception as e:
            logger.warning(f"⚠️ 扫描目录内容失败: {folder_path}, 错误: {e}")
        
        return None
    
    def is_excluded_file(self, filepath: str) -> bool:
        """检查是否应排除该文件"""
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in EXCLUDED_EXTENSIONS:
            return True
        
        # 排除隐藏文件和系统文件
        if filename.startswith('.') or filename.startswith('~'):
            return True
        
        # 排除日志和临时文件
        excluded_names = ['agent.log', 'judge-ai-service.out', 'list.txt', 'Thumbs.db', 'desktop.ini']
        if filename.lower() in [n.lower() for n in excluded_names]:
            return True
        
        return False
    
    def is_supported_file(self, filepath: str) -> bool:
        """检查是否是支持的文件类型"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in SUPPORTED_EXTENSIONS
    
    def detect_category(self, filename: str) -> int:
        """根据文件名检测分类"""
        # 检查前缀编号
        prefix_match = re.match(r'^(\d+)[_\-]', filename)
        if prefix_match:
            prefix_num = int(prefix_match.group(1))
            if prefix_num in PREFIX_NUMBER_CATEGORY:
                return PREFIX_NUMBER_CATEGORY[prefix_num]
        
        # 关键词匹配
        for keyword, category_id in KEYWORD_CATEGORY_MAPPING.items():
            if keyword in filename:
                return category_id
        
        return 4  # 默认：其他文件
    
    def get_or_create_case(self, case_code: str, conn) -> bool:
        """获取或创建案件记录"""
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 检查是否存在
        cursor.execute("SELECT id FROM court_cases WHERE case_code = %s AND isdel = 0", (case_code,))
        row = cursor.fetchone()
        if row:
            return True
        
        if self.dry_run:
            return True
        
        # 解析案号获取信息
        ajlx_mc = None
        if "刑" in case_code:
            ajlx_mc = "刑事"
        elif "行" in case_code:
            ajlx_mc = "行政"
        elif "民" in case_code:
            ajlx_mc = "民事"
        
        trial_stage = None
        if "终" in case_code:
            trial_stage = 2
        elif "初" in case_code:
            trial_stage = 1
        
        region = "佛山"  # 佛山专用脚本，固定区域
        
        try:
            cursor.execute("""
                INSERT INTO court_cases (case_code, ah, aj_mc, ajlx_mc, trial_stage, fymc)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (case_code) DO NOTHING
            """, (case_code, case_code, case_code, ajlx_mc, trial_stage, region))
            conn.commit()
            logger.info(f"✅ 创建新案件: {case_code}")
        except Exception as e:
            logger.error(f"❌ 创建案件失败: {case_code}, 错误: {e}")
            return False
        
        return True
    
    def register_and_import(self, local_path: str, archive_path: str, case_code: str, category_id: int, conn) -> bool:
        """注册资产并导入卷宗"""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        filename = os.path.basename(local_path)
        ext = os.path.splitext(filename)[1].lower()
        
        try:
            if not self.dry_run:
                # 1. 注册到 asset_catalog
                stat = os.stat(local_path)
                md5_hash = self.get_file_md5(local_path)
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                cur.execute("""
                    INSERT INTO asset_catalog (filepath, filename, filesize, file_ext, md5_hash, mtime, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'ready')
                    ON CONFLICT (filepath) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (archive_path, filename, stat.st_size, ext, md5_hash, mtime))
                
                asset_id = cur.fetchone()['id']
                
                # 2. 写入 court_dossiers
                dossier_code = f"{case_code}_{hashlib.md5(archive_path.encode()).hexdigest()[:12]}"
                cur.execute("""
                    INSERT INTO court_dossiers (
                        dossier_code, case_code, asset_id, original_name,
                        original_suffix, dossier_category, classify, sfml
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
                    ON CONFLICT (dossier_code) DO NOTHING
                """, (dossier_code, case_code, asset_id, filename,
                      ext.lstrip('.'), category_id, CATEGORY_MAP.get(category_id, '其他文件')))
                
                conn.commit()
            
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 入库失败: {filename}, 错误: {e}")
            cur.close()
            return False
    
    def move_or_copy_file(self, source: str, target: str) -> bool:
        """移动或复制文件到归档目录"""
        if self.dry_run:
            return True
        
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            if self.no_move:
                shutil.copy2(source, target)
            else:
                shutil.move(source, target)
            return True
        except Exception as e:
            logger.error(f"❌ 文件操作失败: {source} -> {target}, 错误: {e}")
            return False
    
    def extract_zip(self, zip_path: str) -> Optional[str]:
        """解压ZIP文件到同目录"""
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        extract_path = os.path.join(os.path.dirname(zip_path), zip_name)
        
        if os.path.exists(extract_path):
            logger.info(f"📁 已存在解压目录，跳过解压: {zip_name}")
            return extract_path
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for member in zf.namelist():
                    try:
                        decoded_name = member.encode('cp437').decode('gbk')
                    except:
                        decoded_name = member
                    
                    target_path = os.path.join(extract_path, decoded_name)
                    
                    if member.endswith('/'):
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with zf.open(member) as source:
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
            
            self.stats['zips_extracted'] += 1
            return extract_path
        except Exception as e:
            logger.error(f"❌ 解压失败: {zip_path}, 错误: {e}")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(extract_path)
                self.stats['zips_extracted'] += 1
                return extract_path
            except Exception as e2:
                logger.error(f"❌ 简单解压也失败: {e2}")
                return None
    
    def extract_rar(self, rar_path: str) -> Optional[str]:
        """解压RAR文件到同目录"""
        rar_name = os.path.splitext(os.path.basename(rar_path))[0]
        extract_path = os.path.join(os.path.dirname(rar_path), rar_name)
        
        if os.path.exists(extract_path):
            logger.info(f"📁 已存在解压目录，跳过解压: {rar_name}")
            return extract_path
        
        try:
            os.makedirs(extract_path, exist_ok=True)
            result = subprocess.run(
                ['unrar', 'x', '-o+', rar_path, extract_path + '/'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.stats['zips_extracted'] += 1
                return extract_path
            else:
                logger.error(f"❌ unrar 解压失败: {result.stderr}")
                return None
        except FileNotFoundError:
            logger.error("❌ 未安装 unrar，请执行: apt install unrar")
            return None
        except Exception as e:
            logger.error(f"❌ RAR解压失败: {rar_path}, 错误: {e}")
            return None
    
    def process_case_folder(self, case_folder: str, case_code: str) -> int:
        """处理单个案件文件夹"""
        logger.info(f"📁 处理案件: {case_code}")
        
        conn = None
        if not self.dry_run:
            conn = self.connect_db()
            if not self.get_or_create_case(case_code, conn):
                conn.close()
                return 0
        
        imported = 0
        
        for root, dirs, files in os.walk(case_folder):
            for filename in files:
                local_path = os.path.join(root, filename)
                
                if self.is_excluded_file(local_path):
                    self.stats['files_skipped'] += 1
                    continue
                
                if not self.is_supported_file(local_path):
                    self.stats['files_skipped'] += 1
                    continue
                
                category_id = self.detect_category(filename)
                category_name = CATEGORY_MAP.get(category_id, '其他文件')
                
                safe_case_code = case_code.replace('(', '').replace(')', '').replace('/', '_')
                rel_path = os.path.relpath(local_path, case_folder)
                archive_path = os.path.join(self.archive_dir, safe_case_code, rel_path)
                
                if self.dry_run or self.register_and_import(local_path, archive_path, case_code, category_id, conn):
                    imported += 1
                    self.stats['files_imported'] += 1
                    
                    if self.move_or_copy_file(local_path, archive_path):
                        self.stats['files_moved'] += 1
                    
                    self.report_items.append({
                        'status': 'success',
                        'path': local_path,
                        'case_code': case_code,
                        'category': category_name,
                    })
                    logger.info(f"  {'[预览] ' if self.dry_run else ''}✅ {filename} -> {category_name}")
                else:
                    self.stats['errors'] += 1
        
        if conn:
            conn.close()
        self.stats['cases_processed'] += 1
        return imported
    
    def scan_and_import(self, source_dir: str):
        """扫描并导入源目录"""
        logger.info(f"🚀 开始佛山卷宗导入{'（预览模式）' if self.dry_run else ''}")
        logger.info(f"📂 源目录: {source_dir}")
        logger.info(f"📂 归档目录: {self.archive_dir}")
        
        if not os.path.exists(source_dir):
            logger.error(f"❌ 源目录不存在: {source_dir}")
            return
        
        case_items = []
        
        for root, dirs, files in os.walk(source_dir):
            for filename in files:
                file_lower = filename.lower()
                filepath = os.path.join(root, filename)
                
                if file_lower.endswith('.zip'):
                    case_code = self.extract_case_code_from_zip(filename, root)
                    extracted = self.extract_zip(filepath)
                    if extracted:
                        # 如果文件名无法提取案号，尝试从解压目录内部文件提取
                        if not case_code:
                            case_code = self.extract_case_code_from_folder_contents(extracted)
                        if case_code:
                            case_items.append((case_code, extracted))
                        else:
                            logger.warning(f"⚠️ 无法提取案号（含内部扫描）: {filename}")
                
                elif file_lower.endswith('.rar'):
                    case_code = self.extract_case_code_from_zip(filename, root)
                    extracted = self.extract_rar(filepath)
                    if extracted:
                        if not case_code:
                            case_code = self.extract_case_code_from_folder_contents(extracted)
                        if case_code:
                            case_items.append((case_code, extracted))
                        else:
                            logger.warning(f"⚠️ 无法提取案号（含内部扫描）: {filename}")
            
            for dirname in dirs:
                case_code = self.extract_case_code_from_folder(dirname, root)
                if not case_code:
                    folder_path = os.path.join(root, dirname)
                    case_code = self.extract_case_code_from_folder_contents(folder_path)
                if case_code:
                    folder_path = os.path.join(root, dirname)
                    if not any(c == case_code for c, _ in case_items):
                        case_items.append((case_code, folder_path))
        
        unique_cases = {}
        for case_code, folder_path in case_items:
            if case_code not in unique_cases:
                unique_cases[case_code] = folder_path
        
        logger.info(f"📋 发现 {len(unique_cases)} 个案件")
        
        for case_code, folder_path in unique_cases.items():
            self.process_case_folder(folder_path, case_code)
        
        self.print_summary()
    
    def print_summary(self):
        logger.info("=" * 60)
        logger.info(f"📊 导入摘要{'（预览模式）' if self.dry_run else ''}")
        logger.info("=" * 60)
        logger.info(f"处理案件数: {self.stats['cases_processed']}")
        logger.info(f"解压ZIP/RAR数: {self.stats['zips_extracted']}")
        logger.info(f"导入文件数: {self.stats['files_imported']}")
        logger.info(f"移动文件数: {self.stats['files_moved']}")
        logger.info(f"跳过文件数: {self.stats['files_skipped']}")
        logger.info(f"错误数:     {self.stats['errors']}")
        logger.info("=" * 60)
        
        if self.dry_run:
            self.generate_preview_report()
    
    def generate_preview_report(self):
        """生成预览报告"""
        report_path = '/opt/data_asset/logs/foshan_preview_report.md'
        try:
            case_summary = {}
            for item in self.report_items:
                case_code = item['case_code']
                if case_code not in case_summary:
                    case_summary[case_code] = {'files': [], 'categories': {}}
                case_summary[case_code]['files'].append(item)
                cat = item['category']
                case_summary[case_code]['categories'][cat] = case_summary[case_code]['categories'].get(cat, 0) + 1
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# 佛山卷宗导入预览报告\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## 📊 统计摘要\n\n")
                f.write("| 项目 | 数量 |\n")
                f.write("|------|------|\n")
                f.write(f"| 案件数 | {self.stats['cases_processed']} |\n")
                f.write(f"| 待导入文件 | {self.stats['files_imported']} |\n")
                f.write(f"| 解压包数 | {self.stats['zips_extracted']} |\n")
                f.write(f"| 跳过文件 | {self.stats['files_skipped']} |\n")
                f.write(f"| 错误 | {self.stats['errors']} |\n\n")
                
                f.write("## 📁 案件详情\n\n")
                for case_code, data in case_summary.items():
                    f.write(f"### {case_code}\n\n")
                    
                    f.write("**分类统计**: ")
                    cat_parts = [f"{cat}({count})" for cat, count in data['categories'].items()]
                    f.write(" | ".join(cat_parts) + "\n\n")
                    
                    f.write("| 文件名 | 分类 |\n")
                    f.write("|--------|------|\n")
                    for item in data['files'][:20]:
                        fname = os.path.basename(item.get('path', ''))
                        cat = item.get('category', '-')
                        f.write(f"| {fname} | {cat} |\n")
                    if len(data['files']) > 20:
                        f.write(f"| ... 还有 {len(data['files']) - 20} 个文件 | |\n")
                    f.write("\n")
            
            logger.info(f"📄 预览报告已生成: {report_path}")
        except Exception as e:
            logger.error(f"❌ 生成报告失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='佛山法院卷宗导入脚本')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际执行')
    parser.add_argument('--no-move', action='store_true', help='仅入库，不移动文件（复制代替移动）')
    parser.add_argument('--source', type=str, required=True, help='佛山卷宗源目录路径')
    parser.add_argument('--config', type=str, default='/opt/data_asset/config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    importer = FoshanDossierImporter(config_path=args.config)
    importer.dry_run = args.dry_run
    importer.no_move = args.no_move
    importer.scan_and_import(args.source)


if __name__ == '__main__':
    main()
