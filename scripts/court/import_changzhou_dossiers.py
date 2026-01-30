#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法院卷宗导入脚本
import_court_dossiers.py

功能：
1. 扫描 00_Work_Area/new_uploads/ 中的案件文件夹或ZIP
2. 根据目录结构/文件名自动识别文件分类
3. 移动到归档目录 10_Official_Library/01_法院_司法/03_电子卷宗库/
4. 注册到 asset_catalog 表
5. 写入 court_dossiers 表，关联案件

使用方式：
python3 scripts/court/import_court_dossiers.py
python3 scripts/court/import_court_dossiers.py --dry-run  # 预览模式
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
        logging.FileHandler('/opt/data_asset/logs/import_court.log', encoding='utf-8'),
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

# 目录名 -> 分类ID
DIRECTORY_CATEGORY_MAPPING = {
    '起诉状': 1, '诉状': 1,
    '答辩状': 2, '答辩': 2,
    '证据': 3,
    '庭审笔录': 6, '开庭笔录': 6,
    '判决书': 5, '原审判决': 5, '原审材料': 5, '原审法院判决书': 5,
    '立案': 11, '立案登记表': 11,
    '送达回证': 14, '送达': 14,
    '上诉人材料': 3, '被上诉人材料': 3,
    '法院材料': 4,
}

# 文件名关键词 -> 分类ID（长关键词优先）
# 注意：避免使用过短的关键词如"上诉"，会误匹配"上诉人"
KEYWORD_CATEGORY_MAPPING = {
    '起诉状': 1, '诉状': 1,
    '答辩状': 2, '答辩': 2,
    '证据目录': 3, '证据清单': 3, '证据': 3, '合同': 3, '借款': 3, '担保': 3, '凭证': 3, '账户查询': 3, '情况说明': 3,
    '庭审笔录': 6, '开庭笔录': 6, '审理笔录': 6,
    '听证笔录': 16, '听证': 16,
    '谈话笔录': 17, '谈话': 17,
    '调解笔录': 12, '调解协议': 13, '调解': 12,
    '判决书': 5, '判决': 5,
    '立案审批': 11, '立案登记': 11, '立案': 11,
    '送达回证': 14, '送达': 14, '快递单': 14,
    '上诉状': 15,  # 移除"上诉"避免误匹配"上诉人"
    '反诉状': 8,   # 移除"反诉"避免误匹配
}

# 区域代码映射（根据案号中的法院代码）
REGION_CODE_MAP = {
    '0201': '常州', '0202': '天宁', '0203': '钟楼', '0204': '新北', '0206': '武进',
    '0211': '溧阳', '0281': '金坛', '0291': '常州经开',
    '0301': '徐州', '0302': '鼓楼', '0303': '云龙', '0305': '贾汪', '0311': '铜山',
    '0321': '丰县', '0322': '沛县', '0324': '睢宁',
    '0401': '常州', '0501': '苏州', '0502': '沧浪', '0505': '虎丘', '0506': '吴中',
    '0507': '相城', '0508': '姑苏', '0509': '苏州工业园区',
    '0581': '常熟', '0582': '张家港', '0583': '昆山', '0585': '太仓',
    '0601': '南通', '0602': '崇川', '0611': '港闸', '0612': '如皋', '0623': '如东',
    '0681': '启东', '0682': '如东', '0684': '海安', '0685': '海安县',
    '0701': '连云港', '0703': '连云', '0706': '海州', '0721': '赣榆', '0722': '东海',
    '0723': '灌云', '0724': '灌南',
    '0801': '淮安', '0826': '淟水',
    '0901': '盐城', '0902': '亭湖', '0903': '盐都', '0921': '响水', '0923': '阜宁',
    '0924': '射阳', '0925': '建湖', '0981': '东台',
    '1001': '扬州', '1002': '广陵', '1003': '邗江', '1011': '维扬', '1023': '宝应',
    '1081': '仪征', '1084': '高邮',
    '1101': '镇江', '1102': '京口', '1111': '润州', '1112': '丹徒', '1181': '丹阳', 
    '1182': '扬中', '1183': '句容',
    '1201': '泰州', '1202': '海陵', '1203': '高港', '1204': '姜堰',
    '1281': '兴化', '1282': '靖江', '1283': '泰兴',
    '1301': '宿迁', '1302': '宿城', '1321': '沭阳', '1322': '泗洪', '1323': '泗阳',
    '01': '南京', '06': '南通', '02': '常州',
}

SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff'}


class CourtDossierImporter:
    """法院卷宗导入器"""
    
    def __init__(self, config_path='/opt/data_asset/config.yaml'):
        self.config = self._load_config(config_path)
        self.nas_base = self.config.get('nas', {}).get('base_path', '/data/nas_data')
        self.pg_config = self.config.get('postgresql', {})
        
        # 目录配置
        self.upload_dir = os.path.join(self.nas_base, '00_Work_Area', 'new_uploads')
        self.archive_dir = os.path.join(self.nas_base, '10_Official_Library', '01_法院_司法', '03_电子卷宗库')
        
        # 模式控制
        self.dry_run = False
        
        # 统计信息
        self.stats = {
            'cases_processed': 0,
            'files_imported': 0,
            'files_moved': 0,
            'files_skipped': 0,
            'errors': 0,
            'single_files': 0,  # 单文件（无文件夹结构）
        }
        
        # 导入报告详情
        self.report_items = []  # 每个条目: {type, status, path, case_code, category, message}
    
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
    
    def extract_case_code(self, folder_name: str) -> str:
        """从文件夹名提取案号
        
        示例:
        - (2025)苏06民终5226号_1764294652180 -> (2025)苏06民终5226号
        - (2024)苏0612民初240号2025-03-07 -> (2024)苏0612民初240号
        """
        # 匹配完整案号: (年份)法院代码+案件类型+序号+号
        pattern = r'\(\d{4}\)[^\d]+\d+[^\d]+\d+号?'
        match = re.search(pattern, folder_name)
        if match:
            case_code = match.group()
            if not case_code.endswith('号'):
                case_code += '号'
            return case_code
        # 备用模式: 简单匹配
        pattern2 = r'\(\d{4}\)\S+\d+号?'
        match2 = re.search(pattern2, folder_name)
        if match2:
            case_code = match2.group()
            if not case_code.endswith('号'):
                case_code += '号'
            return case_code
        return folder_name
    
    def extract_region(self, case_code: str) -> str:
        """从案号中提取区域
        
        示例:
        - (2025)苏0612民初9559号 -> 如皋 (代码 0612)
        - (2025)苏06民终5226号 -> 南通 (代码 06)
        """
        # 提取4位或者2位区域代码
        match = re.search(r'\(\d{4}\)苏(\d{4}|­\d{2})', case_code)
        if match:
            code = match.group(1)
            return REGION_CODE_MAP.get(code, '未知')
        match2 = re.search(r'\(\d{4}\)苏(\d{2})', case_code)
        if match2:
            code = match2.group(1)
            return REGION_CODE_MAP.get(code, '未知')
        return '未知'
    
    def extract_region_from_path(self, dir_path: str) -> Optional[str]:
        """从目录路径中提取区域
        
        示例:
        - /data/nas_data/.../常州/2024-09-13/4625 -> 常州
        - /data/nas_data/.../南通/2024-09-13/xxx -> 南通
        """
        if not dir_path:
            return None
        
        # 已知区域列表
        known_regions = ['南通', '常州', '如皋', '海门', '启东', '如东', '海安', '通州', '崇川', '港闸', 
                        '无锡', '苏州', '徐州', '盐城', '扬州', '泰州', '镇江', '淮安', '连云港', '宿迁']
        
        # 获取路径中相对于 upload_dir 的部分
        try:
            rel_path = os.path.relpath(dir_path, self.upload_dir)
            path_parts = Path(rel_path).parts
            
            # 遍历路径的每个部分，查找区域名称
            for part in path_parts:
                if part in known_regions:
                    return part
        except:
            pass
        
        return None
    
    def detect_category(self, file_path: str, case_root: str) -> int:
        """根据路径检测分类"""
        rel_path = os.path.relpath(file_path, case_root)
        path_parts = Path(rel_path).parts
        filename_no_ext = os.path.splitext(os.path.basename(file_path))[0]
        
        # 1. 文件名匹配优先（长关键词优先）
        for keyword in sorted(KEYWORD_CATEGORY_MAPPING.keys(), key=len, reverse=True):
            if keyword in filename_no_ext:
                return KEYWORD_CATEGORY_MAPPING[keyword]
        
        # 2. 目录名匹配
        for part in path_parts[:-1]:
            for keyword, category_id in DIRECTORY_CATEGORY_MAPPING.items():
                if keyword in part:
                    return category_id
        
        return 4  # 其他文件
    
    def get_or_create_case(self, case_code: str, conn, dir_path: str = None) -> Optional[str]:
        """获取或创建案件记录
        
        Args:
            case_code: 案件编号
            conn: 数据库连接
            dir_path: 案件所在目录路径（用于提取区域信息）
        """
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT case_code FROM court_cases WHERE case_code = %s", (case_code,))
        if cur.fetchone():
            cur.close()
            return case_code
        
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
        
        # 提取区域：优先从目录路径，其次从案号
        region = self.extract_region_from_path(dir_path) if dir_path else None
        if not region or region == '未知':
            region = self.extract_region(case_code)
        
        try:
            if not self.dry_run:
                cur.execute("""
                    INSERT INTO court_cases (case_code, ah, aj_mc, ajlx_mc, trial_stage, fymc)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (case_code) DO NOTHING
                """, (case_code, case_code, case_code, ajlx_mc, trial_stage, region))
                conn.commit()
            logger.info(f"{'[预览] ' if self.dry_run else ''}✅ 创建新案件: {case_code} (区域: {region})")
            cur.close()
            return case_code
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 创建案件失败: {case_code}, 错误: {e}")
            cur.close()
            return None
    
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
    
    def move_file(self, source: str, target: str) -> bool:
        """移动文件"""
        if self.dry_run:
            logger.info(f"[预览] 移动: {os.path.basename(source)} -> {os.path.dirname(target)}")
            return True
        
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.move(source, target)
            return True
        except Exception as e:
            logger.error(f"❌ 移动失败: {source}, 错误: {e}")
            return False
    
    def process_case_folder(self, case_folder: str) -> int:
        """处理单个案件文件夹"""
        folder_name = os.path.basename(case_folder)
        case_code = self.extract_case_code(folder_name)
        
        logger.info(f"📁 处理案件: {case_code}")
        
        conn = self.connect_db()
        if not self.get_or_create_case(case_code, conn, case_folder):
            conn.close()
            return 0
        
        imported = 0
        
        for root, dirs, files in os.walk(case_folder):
            for filename in files:
                local_path = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext not in SUPPORTED_EXTENSIONS:
                    self.stats['files_skipped'] += 1
                    continue
                
                category_id = self.detect_category(local_path, case_folder)
                category_name = CATEGORY_MAP.get(category_id, '其他文件')
                
                # 构建归档路径
                rel_path = os.path.relpath(local_path, case_folder)
                archive_path = os.path.join(self.archive_dir, folder_name, rel_path)
                
                # 入库
                if self.register_and_import(local_path, archive_path, case_code, category_id, conn):
                    imported += 1
                    self.stats['files_imported'] += 1
                    
                    # 移动文件
                    if self.move_file(local_path, archive_path):
                        self.stats['files_moved'] += 1
                    
                    self.report_items.append({
                        'type': 'folder_file',
                        'status': 'success',
                        'path': local_path,
                        'case_code': case_code,
                        'category': category_name,
                        'message': ''
                    })
                    logger.info(f"  {'[预览] ' if self.dry_run else ''}✅ {filename} -> {category_name}")
                else:
                    self.stats['errors'] += 1
                    self.report_items.append({
                        'type': 'folder_file',
                        'status': 'error',
                        'path': local_path,
                        'case_code': case_code,
                        'category': category_name,
                        'message': '导入失败'
                    })
        
        conn.close()
        self.stats['cases_processed'] += 1
        
        # 清理空目录
        if not self.dry_run and os.path.exists(case_folder):
            try:
                shutil.rmtree(case_folder)
                logger.info(f"  🗑️ 清理源目录: {folder_name}")
            except:
                pass
        
        return imported
    
    def extract_zip(self, zip_path: str) -> Optional[str]:
        """解压ZIP文件"""
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        extract_path = os.path.join(os.path.dirname(zip_path), zip_name)
        
        logger.info(f"📦 解压: {os.path.basename(zip_path)}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_path)
            
            # 删除ZIP文件
            if not self.dry_run:
                os.remove(zip_path)
            
            return extract_path
        except Exception as e:
            logger.error(f"❌ 解压失败: {zip_path}, 错误: {e}")
            return None
    
    def run(self):
        """运行导入流程"""
        logger.info(f"🚀 开始法院卷宗导入{'（预览模式）' if self.dry_run else ''}")
        logger.info(f"📂 上传目录: {self.upload_dir}")
        logger.info(f"📂 归档目录: {self.archive_dir}")
        
        if not os.path.exists(self.upload_dir):
            logger.error(f"❌ 上传目录不存在: {self.upload_dir}")
            return
        
        # 递归扫描上传目录及所有子目录
        case_items = []
        
        for root, dirs, files in os.walk(self.upload_dir):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # 检查当前目录下的 ZIP 文件
            for filename in files:
                if filename.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, filename)
                
                if filename.lower().endswith('.zip'):
                    # ZIP 文件 - 检查是否包含案号
                    if re.search(r'\(\d{4}\)', filename):
                        # 解压 ZIP
                        extracted = self.extract_zip(file_path)
                        if extracted:
                            case_items.append(('folder', extracted))
                    else:
                        # 尝试从 ZIP 名称直接作为案号（如 4625.zip）
                        extracted = self.extract_zip(file_path)
                        if extracted:
                            case_items.append(('folder', extracted))
                elif os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS:
                    # 单个文件（如 word/pdf）
                    if re.search(r'\(\d{4}\)', filename):
                        case_items.append(('file', file_path))
                    else:
                        self.report_items.append({
                            'type': 'single_file',
                            'status': 'skipped',
                            'path': file_path,
                            'case_code': '',
                            'category': '',
                            'message': '文件名中未找到案号格式'
                        })
                        self.stats['files_skipped'] += 1
            
            # 检查当前目录下的案件文件夹（包含案号格式）
            for dirname in dirs[:]:  # 使用副本避免修改时问题
                dir_path = os.path.join(root, dirname)
                if re.search(r'\(\d{4}\)', dirname):
                    case_items.append(('folder', dir_path))
                    # 从递归列表中移除，避免再次进入
                    dirs.remove(dirname)
        
        logger.info(f"📋 发现 {len(case_items)} 个案件/文件")
        
        for item_type, item_path in case_items:
            if item_type == 'folder':
                self.process_case_folder(item_path)
            else:
                self.process_single_file(item_path)
        
        self.print_summary()
        self.generate_report()
    
    def process_single_file(self, file_path: str):
        """处理单个文件（无文件夹结构）"""
        filename = os.path.basename(file_path)
        case_code = self.extract_case_code(filename)
        
        logger.info(f"📄 处理单文件: {filename} -> 案号: {case_code}")
        
        conn = self.connect_db()
        if not self.get_or_create_case(case_code, conn):
            self.report_items.append({
                'type': 'single_file',
                'status': 'error',
                'path': file_path,
                'case_code': case_code,
                'category': '',
                'message': '创建案件失败'
            })
            conn.close()
            return
        
        category_id = self.detect_category(file_path, os.path.dirname(file_path))
        category_name = CATEGORY_MAP.get(category_id, '其他文件')
        
        # 构建归档路径（单文件放到案号目录下）
        folder_name = case_code.replace('/', '_').replace('\\', '_')
        archive_path = os.path.join(self.archive_dir, folder_name, filename)
        
        if self.register_and_import(file_path, archive_path, case_code, category_id, conn):
            self.stats['files_imported'] += 1
            self.stats['single_files'] += 1
            
            if self.move_file(file_path, archive_path):
                self.stats['files_moved'] += 1
            
            self.report_items.append({
                'type': 'single_file',
                'status': 'success',
                'path': file_path,
                'case_code': case_code,
                'category': category_name,
                'message': ''
            })
            logger.info(f"  {'[预览] ' if self.dry_run else ''}✅ {filename} -> {category_name}")
        else:
            self.stats['errors'] += 1
            self.report_items.append({
                'type': 'single_file',
                'status': 'error',
                'path': file_path,
                'case_code': case_code,
                'category': category_name,
                'message': '导入失败'
            })
        
        conn.close()
    
    def print_summary(self):
        logger.info("=" * 60)
        logger.info(f"📊 导入摘要{'（预览模式）' if self.dry_run else ''}")
        logger.info("=" * 60)
        logger.info(f"处理案件数: {self.stats['cases_processed']}")
        logger.info(f"导入文件数: {self.stats['files_imported']}")
        logger.info(f"  - 单文件:  {self.stats['single_files']}")
        logger.info(f"移动文件数: {self.stats['files_moved']}")
        logger.info(f"跳过文件数: {self.stats['files_skipped']}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info("=" * 60)
    
    def generate_report(self):
        """生成导入报告"""
        import json
        from datetime import datetime
        
        # 报告放到项目根目录
        report_dir = '/opt/data_asset/reports/court'
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(report_dir, f'import_report_{timestamp}.json')
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'summary': self.stats,
            'items': self.report_items,
            'errors': [i for i in self.report_items if i['status'] == 'error'],
            'skipped': [i for i in self.report_items if i['status'] == 'skipped'],
        }
        
        if not self.dry_run:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"📄 报告已生成: {report_file}")
        
        # 打印异常摘要
        if report['errors']:
            logger.warning(f"⚠️ 存在 {len(report['errors'])} 个导入错误:")
            for item in report['errors'][:5]:
                logger.warning(f"   - {item['path']}: {item['message']}")
        
        if report['skipped']:
            logger.warning(f"⚠️ 跳过 {len(report['skipped'])} 个文件:")
            for item in report['skipped'][:5]:
                logger.warning(f"   - {item['path']}: {item['message']}")


def main():
    parser = argparse.ArgumentParser(description='法院卷宗导入脚本')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际执行')
    parser.add_argument('--config', type=str, default='/opt/data_asset/config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    importer = CourtDossierImporter(config_path=args.config)
    importer.dry_run = args.dry_run
    importer.run()


if __name__ == '__main__':
    main()

