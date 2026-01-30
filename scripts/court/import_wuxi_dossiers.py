#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无锡法院卷宗导入脚本
import_wuxi_dossiers.py

功能：
1. 扫描无锡法院目录下的案件ZIP/7z文件和解压后的文件夹
2. 自动解压ZIP/RAR/7z文件，过滤日志、Excel等非卷宗文件
3. 根据文件名自动识别分类
4. 导入到 court_cases 和 court_dossiers 表

无锡目录结构特点：
- 多种法院代码: 02(中院)/0211(滨湖)
- ZIP压缩包: (2023)苏02民初81号.zip
- 已解压文件夹: (2023)苏02民初81号/
- 混杂文件: .log, .out, .docx

使用方式：
python3 scripts/court/import_wuxi_dossiers.py
python3 scripts/court/import_wuxi_dossiers.py --dry-run  # 预览模式
python3 scripts/court/import_wuxi_dossiers.py --source /path/to/无锡目录
"""

import os
import re
import sys
import hashlib
import zipfile
import shutil
import logging
import argparse
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
        logging.FileHandler('/opt/data_asset/logs/import_wuxi.log', encoding='utf-8'),
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

# 文件名前缀编号 -> 分类ID（东台特有格式：0_起诉状.pdf, 1_证据.pdf）
PREFIX_NUMBER_CATEGORY = {
    0: 1,   # 0_ 通常是起诉状或调解协议
    1: 1,   # 1_ 起诉状
    2: 12,  # 2_ 调解笔录
}

# 文件名关键词 -> 分类ID
KEYWORD_CATEGORY_MAPPING = {
    '起诉状': 1, '诉状': 1,
    '答辩状': 2, '答辩': 2,
    '证据目录': 3, '证据清单': 3, '证据': 3, '合同': 3, '借款': 3, '担保': 3,
    '凭证': 3, '账户查询': 3, '情况说明': 3, '保险单': 3, '保险': 3,
    '身份证': 3, '营业执照': 3, '授权委托书': 3, '委托书': 3,
    '诊断证明': 3, '病历': 3, '鉴定': 3, '工伤': 3,
    '庭审笔录': 6, '开庭笔录': 6, '审理笔录': 6,
    '听证笔录': 16, '听证': 16,
    '谈话笔录': 17, '谈话': 17,
    '调解笔录': 12, '调解协议': 13, '调解': 12,
    '判决书': 5, '民事判决': 5, '判决': 5,
    '立案审批': 11, '立案登记': 11, '立案': 11,
    '送达回证': 14, '送达': 14, '快递单': 14, '送达地址': 14,
    '上诉状': 15,
    '反诉状': 8,
    '拒赔': 3, '拒付': 3,
}

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff'}

# 需要排除的文件类型
EXCLUDED_EXTENSIONS = {'.log', '.out', '.xlsx', '.xls', '.rar', '.zip', '.7z'}

# 需要排除的文件名模式
EXCLUDED_PATTERNS = [
    r'agent\.log',
    r'judge-ai-service\.out',
    r'\.log\.\d+$',
    r'系统使用量',
    r'电话表',
    r'账号汇总',
]

class WuxiDossierImporter:
    """无锡法院卷宗导入器"""
    
    def __init__(self, config_path='/opt/data_asset/config.yaml'):
        self.config = self._load_config(config_path)
        self.nas_base = self.config.get('nas', {}).get('base_path', '/data/nas_data')
        self.pg_config = self.config.get('postgresql', {})
        
        # 目录配置
        self.archive_dir = os.path.join(self.nas_base, '10_Official_Library', '01_法院_司法', '03_电子卷宗库')
        
        # 源目录（运行时指定）
        self.source_dir = None
        
        # 模式控制
        self.dry_run = False
        self.no_move = False  # 是否不移动文件（仅入库）
        
        # 统计信息
        self.stats = {
            'cases_processed': 0,
            'files_imported': 0,
            'files_moved': 0,
            'files_skipped': 0,
            'zips_extracted': 0,
            'errors': 0,
        }
        
        # 导入报告详情
        self.report_items = []
    
    def _load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
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
            database=self.pg_config.get('database', 'asset_catalog')
        )
    
    def calculate_md5(self, filepath: str) -> str:
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_case_code_from_zip(self, zip_name: str, parent_path: str = None) -> Optional[str]:
        """从ZIP/RAR文件名提取案号（保留日期作为案号一部分）
        
        示例:
        - 2025苏0981民初858号2025-05-21.zip -> (2025)苏0981民初858号2025-05-21
        - (2025)苏0981民初858号2025-05-21.zip -> (2025)苏0981民初858号2025-05-21
        - 1817.rar -> 1817 (纯数字直接作为案号)
        """
        # 匹配格式（含日期）: 2025苏0981民初858号2025-05-21
        pattern1 = r'(\d{4})苏(\d{4})(\w+)(\d+)号(\d{4}-\d{2}-\d{2})?'
        match = re.search(pattern1, zip_name)
        if match:
            year, court, case_type, num, date = match.groups()
            case_code = f"({year})苏{court}{case_type}{num}号"
            if date:
                case_code += "_" + date  # 保留日期作为案号一部分，用下划线分隔
            return case_code
        
        # 匹配格式（含日期）: (2025)苏0981民初858号2025-05-21
        pattern2 = r'\((\d{4})\)苏(\d{4})(\w+)(\d+)号(\d{4}-\d{2}-\d{2})?'
        match2 = re.search(pattern2, zip_name)
        if match2:
            year, court, case_type, num, date = match2.groups()
            case_code = f"({year})苏{court}{case_type}{num}号"
            if date:
                case_code += "_" + date
            return case_code
        
        # 匹配纯数字文件名（如 1817.rar, 2172.zip）
        # 纯数字直接作为案号使用
        base_name = os.path.splitext(zip_name)[0]
        pure_num_pattern = r'^(\d{3,5})$'  # 3-5位纯数字
        match3 = re.match(pure_num_pattern, base_name)
        if match3:
            case_num = match3.group(1)
            # 纯数字直接作为案号
            return case_num
        
        return None
    
    def extract_case_code_from_folder(self, folder_name: str, parent_path: str = None) -> Optional[str]:
        """从文件夹名提取案号（保留日期作为案号一部分）
        
        示例:
        - (2025)苏0981民初858号2025-05-21 -> (2025)苏0981民初858号2025-05-21
        - 1817 -> 1817
        """
        # 匹配完整格式（含日期）: (2025)苏0981民初858号2025-05-21
        pattern_with_date = r'\((\d{4})\)苏(\d{4})(\w+)(\d+)号(\d{4}-\d{2}-\d{2})?'
        match = re.search(pattern_with_date, folder_name)
        if match:
            year, court, case_type, num, date = match.groups()
            case_code = f"({year})苏{court}{case_type}{num}号"
            if date:
                case_code += "_" + date  # 保留日期作为案号一部分，用下划线分隔
            return case_code
        
        # 匹配纯数字文件夹名（如 1817, 2172）
        pure_num_pattern = r'^(\d{3,5})$'  # 3-5位纯数字
        match2 = re.match(pure_num_pattern, folder_name)
        if match2:
            case_num = match2.group(1)
            # 纯数字直接作为案号
            return case_num
        
        return None
    
    def is_excluded_file(self, filepath: str) -> bool:
        """检查是否应排除该文件"""
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        
        # 扩展名排除
        if ext in EXCLUDED_EXTENSIONS:
            return True
        
        # 模式排除
        for pattern in EXCLUDED_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        
        return False
    
    def is_supported_file(self, filepath: str) -> bool:
        """检查是否是支持的文件类型"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in SUPPORTED_EXTENSIONS
    
    def detect_category(self, filename: str) -> int:
        """根据文件名检测分类"""
        filename_no_ext = os.path.splitext(filename)[0]
        
        # 1. 检查前缀编号（东台特有：0_xxx.pdf, 1_xxx.pdf）
        prefix_match = re.match(r'^(\d+)_', filename_no_ext)
        if prefix_match:
            prefix_num = int(prefix_match.group(1))
            # 去掉前缀后再匹配关键词
            remaining = filename_no_ext[len(prefix_match.group(0)):]
            for keyword in sorted(KEYWORD_CATEGORY_MAPPING.keys(), key=len, reverse=True):
                if keyword in remaining:
                    return KEYWORD_CATEGORY_MAPPING[keyword]
        
        # 2. 关键词匹配（长关键词优先）
        for keyword in sorted(KEYWORD_CATEGORY_MAPPING.keys(), key=len, reverse=True):
            if keyword in filename_no_ext:
                return KEYWORD_CATEGORY_MAPPING[keyword]
        
        return 4  # 其他文件
    
    def get_or_create_case(self, case_code: str, conn) -> bool:
        """获取或创建案件记录"""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT case_code FROM court_cases WHERE case_code = %s", (case_code,))
        if cur.fetchone():
            cur.close()
            return True
        
        # 解析案件类型（只有能从案号中明确识别时才设置，否则为空）
        ajlx_mc = None
        if "刑" in case_code:
            ajlx_mc = "刑事"
        elif "行" in case_code:
            ajlx_mc = "行政"
        elif "民" in case_code:
            ajlx_mc = "民事"
        
        # 解析审判阶段（只有能从案号中明确识别时才设置）
        trial_stage = None
        if "终" in case_code:
            trial_stage = 2  # 二审
        elif "初" in case_code:
            trial_stage = 1  # 一审
        
        region = "无锡"  # 无锡专用脚本，固定区域
        
        try:
            if not self.dry_run:
                cur.execute("""
                    INSERT INTO court_cases (case_code, ah, aj_mc, ajlx_mc, trial_stage, fymc)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (case_code) DO NOTHING
                """, (case_code, case_code, case_code, ajlx_mc, trial_stage, region))
                conn.commit()
            logger.info(f"{'[预览] ' if self.dry_run else ''}✅ 创建新案件: {case_code}")
            cur.close()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 创建案件失败: {case_code}, 错误: {e}")
            cur.close()
            return False
    
    def register_and_import(self, local_path: str, archive_path: str,
                            case_code: str, category_id: int, conn) -> bool:
        """注册资产并导入卷宗"""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        filename = os.path.basename(local_path)
        ext = os.path.splitext(filename)[1].lower()
        
        try:
            if not self.dry_run:
                # 1. 注册到 asset_catalog
                stat = os.stat(local_path)
                md5_hash = self.calculate_md5(local_path)
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
        """移动或复制文件"""
        if self.dry_run:
            logger.info(f"[预览] 移动: {os.path.basename(source)} -> {os.path.dirname(target)}")
            return True
        
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if self.no_move:
                shutil.copy2(source, target)
            else:
                shutil.move(source, target)
            return True
        except Exception as e:
            logger.error(f"❌ 移动/复制失败: {source}, 错误: {e}")
            return False
    
    def extract_zip(self, zip_path: str) -> Optional[str]:
        """解压ZIP文件到同目录"""
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        extract_path = os.path.join(os.path.dirname(zip_path), zip_name)
        
        # 如果已解压目录存在，跳过
        if os.path.exists(extract_path):
            logger.info(f"📁 已存在解压目录，跳过解压: {zip_name}")
            return extract_path
        
        logger.info(f"📦 解压: {os.path.basename(zip_path)}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # 处理可能的编码问题
                for member in zf.namelist():
                    try:
                        # 尝试修复中文文件名编码
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
            # 尝试简单解压
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(extract_path)
                self.stats['zips_extracted'] += 1
                return extract_path
            except Exception as e2:
                logger.error(f"❌ 简单解压也失败: {e2}")
                return None
    
    def extract_rar(self, rar_path: str) -> Optional[str]:
        """解压RAR文件到同目录（需要安装unrar）"""
        rar_name = os.path.splitext(os.path.basename(rar_path))[0]
        extract_path = os.path.join(os.path.dirname(rar_path), rar_name)
        
        # 如果已解压目录存在，跳过
        if os.path.exists(extract_path):
            logger.info(f"📁 已存在解压目录，跳过解压: {rar_name}")
            return extract_path
        
        logger.info(f"📦 解压RAR: {os.path.basename(rar_path)}")
        
        try:
            import subprocess
            os.makedirs(extract_path, exist_ok=True)
            # 使用 unrar 命令解压
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
    
    def extract_7z(self, archive_path: str) -> Optional[str]:
        """解压7z文件到同目录（需要安装p7zip-full）"""
        archive_name = os.path.splitext(os.path.basename(archive_path))[0]
        extract_path = os.path.join(os.path.dirname(archive_path), archive_name)
        
        # 如果已解压目录存在，跳过
        if os.path.exists(extract_path):
            logger.info(f"📁 已存在解压目录，跳过解压: {archive_name}")
            return extract_path
        
        logger.info(f"📦 解压7z: {os.path.basename(archive_path)}")
        
        try:
            import subprocess
            os.makedirs(extract_path, exist_ok=True)
            # 使用 7z 命令解压
            result = subprocess.run(
                ['7z', 'x', archive_path, f'-o{extract_path}', '-y'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.stats['zips_extracted'] += 1
                return extract_path
            else:
                logger.error(f"❌ 7z 解压失败: {result.stderr}")
                return None
        except FileNotFoundError:
            logger.error("❌ 未安装 7z，请执行: apt install p7zip-full")
            return None
        except Exception as e:
            logger.error(f"❌ 7z解压失败: {archive_path}, 错误: {e}")
            return None
    
    def process_case_folder(self, case_folder: str, case_code: str) -> int:
        """处理单个案件文件夹"""
        logger.info(f"📁 处理案件: {case_code}")
        
        conn = self.connect_db()
        if not self.get_or_create_case(case_code, conn):
            conn.close()
            return 0
        
        imported = 0
        folder_name = os.path.basename(case_folder)
        
        for root, dirs, files in os.walk(case_folder):
            for filename in files:
                local_path = os.path.join(root, filename)
                
                # 排除检查
                if self.is_excluded_file(local_path):
                    self.stats['files_skipped'] += 1
                    continue
                
                # 支持检查
                if not self.is_supported_file(local_path):
                    self.stats['files_skipped'] += 1
                    continue
                
                category_id = self.detect_category(filename)
                category_name = CATEGORY_MAP.get(category_id, '其他文件')
                
                # 构建归档路径（使用案号作为目录名）
                safe_case_code = case_code.replace('(', '').replace(')', '').replace('/', '_')
                rel_path = os.path.relpath(local_path, case_folder)
                archive_path = os.path.join(self.archive_dir, safe_case_code, rel_path)
                
                # 入库
                if self.register_and_import(local_path, archive_path, case_code, category_id, conn):
                    imported += 1
                    self.stats['files_imported'] += 1
                    
                    # 移动/复制文件
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
        
        conn.close()
        self.stats['cases_processed'] += 1
        return imported
    
    def scan_and_import(self, source_dir: str):
        """扫描并导入源目录"""
        logger.info(f"🚀 开始无锡卷宗导入{'（预览模式）' if self.dry_run else ''}")
        logger.info(f"📂 源目录: {source_dir}")
        logger.info(f"📂 归档目录: {self.archive_dir}")
        
        if not os.path.exists(source_dir):
            logger.error(f"❌ 源目录不存在: {source_dir}")
            return
        
        # 收集所有案件
        case_items = []  # (case_code, folder_path)
        
        for root, dirs, files in os.walk(source_dir):
            # 处理 ZIP 和 RAR 文件
            for filename in files:
                file_lower = filename.lower()
                filepath = os.path.join(root, filename)
                
                # 处理 ZIP 文件
                if file_lower.endswith('.zip'):
                    case_code = self.extract_case_code_from_zip(filename, root)
                    if case_code:
                        extracted = self.extract_zip(filepath)
                        if extracted:
                            case_items.append((case_code, extracted))
                    else:
                        logger.warning(f"⚠️ 无法从ZIP文件名提取案号: {filename}")
                
                # 处理 RAR 文件
                elif file_lower.endswith('.rar'):
                    case_code = self.extract_case_code_from_zip(filename, root)  # 复用同样的提取逻辑
                    if case_code:
                        extracted = self.extract_rar(filepath)
                        if extracted:
                            case_items.append((case_code, extracted))
                    else:
                        logger.warning(f"⚠️ 无法从RAR文件名提取案号: {filename}")
                
                # 处理 7z 文件
                elif file_lower.endswith('.7z'):
                    case_code = self.extract_case_code_from_zip(filename, root)  # 复用同样的提取逻辑
                    if case_code:
                        extracted = self.extract_7z(filepath)
                        if extracted:
                            case_items.append((case_code, extracted))
                    else:
                        logger.warning(f"⚠️ 无法从7z文件名提取案号: {filename}")
            
            # 处理已解压的文件夹
            for dirname in dirs:
                case_code = self.extract_case_code_from_folder(dirname, root)
                if case_code:
                    folder_path = os.path.join(root, dirname)
                    # 检查是否已在列表中（避免重复）
                    if not any(c == case_code for c, _ in case_items):
                        case_items.append((case_code, folder_path))
        
        # 去重
        unique_cases = {}
        for case_code, folder_path in case_items:
            if case_code not in unique_cases:
                unique_cases[case_code] = folder_path
        
        logger.info(f"📋 发现 {len(unique_cases)} 个案件")
        
        # 处理每个案件
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
        
        # 生成预览报告
        if self.dry_run:
            self.generate_preview_report()
    
    def generate_preview_report(self):
        """生成预览报告（Markdown格式）"""
        report_path = '/opt/data_asset/logs/wuxi_preview_report.md'
        
        try:
            # 按案件分组统计
            case_summary = {}
            for item in self.report_items:
                case_code = item.get('case_code', '未知')
                if case_code not in case_summary:
                    case_summary[case_code] = {'files': [], 'categories': {}}
                case_summary[case_code]['files'].append(item)
                cat = item.get('category', '其他')
                case_summary[case_code]['categories'][cat] = case_summary[case_code]['categories'].get(cat, 0) + 1
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# 无锡卷宗导入预览报告\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 统计摘要
                f.write("## 📊 统计摘要\n\n")
                f.write(f"| 指标 | 数量 |\n")
                f.write(f"|------|------|\n")
                f.write(f"| 案件数 | {self.stats['cases_processed']} |\n")
                f.write(f"| 解压包数 | {self.stats['zips_extracted']} |\n")
                f.write(f"| 待导入文件 | {self.stats['files_imported']} |\n")
                f.write(f"| 跳过文件 | {self.stats['files_skipped']} |\n")
                f.write(f"| 错误 | {self.stats['errors']} |\n\n")
                
                # 按案件详细列表
                f.write("## 📁 案件详情\n\n")
                for case_code, data in case_summary.items():
                    f.write(f"### {case_code}\n\n")
                    
                    # 分类统计
                    f.write("**分类统计**: ")
                    cat_parts = [f"{cat}({count})" for cat, count in data['categories'].items()]
                    f.write(" | ".join(cat_parts) + "\n\n")
                    
                    # 文件列表
                    f.write("| 文件名 | 分类 |\n")
                    f.write("|--------|------|\n")
                    for item in data['files'][:20]:  # 每个案件最多显示20个文件
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
    parser = argparse.ArgumentParser(description='无锡法院卷宗导入脚本')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际执行')
    parser.add_argument('--no-move', action='store_true', help='仅入库，不移动文件（复制代替移动）')
    parser.add_argument('--source', type=str, required=True, help='无锡卷宗源目录路径')
    parser.add_argument('--config', type=str, default='/opt/data_asset/config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    importer = WuxiDossierImporter(config_path=args.config)
    importer.dry_run = args.dry_run
    importer.no_move = args.no_move
    importer.scan_and_import(args.source)


if __name__ == '__main__':
    main()
