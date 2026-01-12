#!/usr/bin/env python3
"""
文件规范检测和整理脚本
verify_structure.py

功能：
1. 检测 00_Work_Area/new_uploads/ 中的文件
2. 验证文件命名和目录结构是否符合规范
3. 将合规文件移动到 10_Official_Library/
4. 将不合规文件保留或移到 trash_bin/
5. 记录操作日志到PostgreSQL
"""

import os
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import Json
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/data_asset/logs/verify_structure.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FileStructureVerifier:
    """文件结构验证器"""
    
    def __init__(self, config_path='/opt/data_asset/config.yaml'):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.nas_base = self.config['nas']['base_path']
        self.work_area = os.path.join(self.nas_base, '00_Work_Area')
        self.official_lib = os.path.join(self.nas_base, '10_Official_Library')
        
        # PostgreSQL连接
        self.pg_config = self.config['postgresql']
        
        # 文件命名规范
        self.naming_rules = self.config['naming_rules']
        
        # 统计信息
        self.stats = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'moved': 0,
            'errors': 0
        }
        
        # 元数据
        self.metadata = {}
    
    def connect_db(self):
        """连接PostgreSQL"""
        return psycopg2.connect(
            host=self.pg_config['host'],
            port=self.pg_config['port'],
            user=self.pg_config['user'],
            password=self.pg_config['password'],
            database=self.pg_config['database']
        )
    
    def validate_filename(self, filename: str, file_type: str) -> Tuple[bool, str]:
        """
        验证文件名是否符合规范
        
        Args:
            filename: 文件名
            file_type: 文件类型（alarm_image/channel_image）
        
        Returns:
            (是否合规, 错误信息或设备编码)
        """
        rules = self.naming_rules.get(file_type, {})
        
        if not rules:
            return True, ""  # 没有规则则通过
        
        # 检查文件扩展名
        allowed_exts = rules.get('allowed_extensions', [])
        file_ext = Path(filename).suffix.lower()
        if allowed_exts and file_ext not in allowed_exts:
            return False, f"文件扩展名 {file_ext} 不在允许列表 {allowed_exts} 中"
        
        # 检查命名模式
        pattern = rules.get('pattern')
        if pattern:
            if not re.match(pattern, filename):
                description = rules.get('description', pattern)
                return False, f"文件名不符合规范: {description}"
            
            # 提取设备编码（从文件名中提取）
            # 例如：alarm_001e67b2f0411310030522.jpg -> 001e67b2f0411310030522
            try:
                prefix = file_type.split('_')[0]  # alarm 或 channel
                name_without_ext = Path(filename).stem
                if name_without_ext.startswith(f"{prefix}_"):
                    device_code = name_without_ext.split(f"{prefix}_", 1)[1]
                    # 验证设备编码（只能包含字母和数字）
                    if not re.match(r'^[a-zA-Z0-9]+$', device_code):
                        return False, f"设备编码包含非法字符: {device_code}"
                else:
                    return False, f"文件名必须以 {prefix}_ 开头"
            except:
                return False, "无法解析设备编码"
        
        # 检查文件名长度
        max_length = rules.get('max_length', 255)
        if len(filename) > max_length:
            return False, f"文件名过长（{len(filename)} > {max_length}）"
        
        # 检查非法字符
        illegal_chars = rules.get('illegal_chars', [])
        for char in illegal_chars:
            if char in filename:
                return False, f"文件名包含非法字符: {char}"
        
        return True, ""
    
    
    def load_metadata(self):
        """
        加载元数据文件
        
        支持CSV格式：filename,alarm_name,analysis_result,alarm_time,device_code,category
        """
        metadata_file = os.path.join(self.work_area, 'new_uploads', 'metadata_emergency.csv')
        
        if not os.path.exists(metadata_file):
            logger.warning("⚠️ 未找到metadata_emergency.csv，将使用默认分类（未分类）")
            return {}
        
        import csv
        metadata = {}
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    filename = row['filename']
                    
                    # 如果同一文件名已存在，追加到列表（支持多重告警）
                    if filename not in metadata:
                        metadata[filename] = []
                    
                    # 追加记录到列表
                    metadata[filename].append({
                        'alarm_name': row.get('alarm_name', '未分类'),
                        'analysis_result': row.get('analysis_result', ''),
                        'alarm_time': row.get('alarm_time', ''),
                        'device_code': row.get('device_code', ''),
                        'category': row.get('category', '历史告警归档')
                    })
            
            # 统计总记录数
            total_records = sum(len(records) for records in metadata.values())
            logger.info(f"📋 已加载 {len(metadata)} 个文件的 {total_records} 条元数据记录")
            return metadata
            
        except Exception as e:
            logger.error(f"读取metadata_emergency.csv失败: {e}")
            return {}
    
    def parse_target_path(self, filename: str, source_dir: str) -> Dict:
        """
        根据文件名和元数据解析目标路径
        
        支持：
        1. 多重告警组合命名（如"火点检测+烟火检测+烟雾检测"）
        2. 从metadata读取category字段
        3. 灵活的时间解析
        
        Args:
            filename: 文件名
            source_dir: 来源目录
        
        Returns:
            {
                'industry': '应急_安全',
                'category': '历史告警归档',
                'subcategory': '烟雾检测',
                'year': 2025,
                'quarter': '2025_Q4',
                'target_path': '/data/nas_data/...'
            }
        """
        # 获取该文件的所有元数据记录（metadata中每个文件名对应一个列表）
        file_records = self.metadata.get(filename, [])
        
        # 如果有多条记录（多重告警）
        if len(file_records) > 1:
            # 组合所有告警类型名称，按字母顺序排序
            alarm_types = sorted(set(
                rec.get('alarm_name', '未分类') 
                for rec in file_records
            ))
            subcategory = '+'.join(alarm_types)
            
            # 取最早的时间
            alarm_times = [
                rec.get('alarm_time', '') 
                for rec in file_records 
                if rec.get('alarm_time')
            ]
            alarm_time_str = min(alarm_times) if alarm_times else ''
        elif len(file_records) == 1:
            # 单一告警
            subcategory = file_records[0].get('alarm_name', '未分类')
            alarm_time_str = file_records[0].get('alarm_time', '')
        else:
            # 没有元数据，使用默认值
            subcategory = '未分类'
            alarm_time_str = ''
        
        # 从元数据获取category（默认：历史告警归档）
        category = file_records[0].get('category', '历史告警归档') if file_records else '历史告警归档'
        
        # 解析时间
        if alarm_time_str:
            try:
                from dateutil import parser
                alarm_time = parser.parse(alarm_time_str)
                year = alarm_time.year
                quarter = f"{year}_Q{(alarm_time.month-1)//3 + 1}"
            except Exception as e:
                logger.warning(f"时间解析失败: {alarm_time_str}，错误: {e}，使用当前时间")
                year = datetime.now().year
                quarter = f"{year}_Q{(datetime.now().month-1)//3 + 1}"
        else:
            year = datetime.now().year
            quarter = f"{year}_Q{(datetime.now().month-1)//3 + 1}"
        
        # 构建目标路径
        target_path = os.path.join(
            self.official_lib,
            "02_应急_安全",
            f"02_{category}",
            subcategory,
            quarter
        )
        
        result = {
            'industry': '应急_安全',
            'category': category,
            'subcategory': subcategory,
            'year': year,
            'quarter': quarter,
            'target_path': target_path
        }
        
        return result
    
    def move_file(self, source: str, target: str, operation_type='move') -> bool:
        """移动文件并记录操作日志"""
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # 移动文件
            shutil.move(source, target)
            
            # 记录到PostgreSQL
            self.log_operation(
                operation_type=operation_type,
                filepath_old=source,
                filepath_new=target,
                status='success'
            )
            
            logger.info(f"✅ 移动文件: {source} -> {target}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 移动文件失败: {source} -> {target}, 错误: {e}")
            self.log_operation(
                operation_type=operation_type,
                filepath_old=source,
                filepath_new=target,
                status='failed',
                error_msg=str(e)
            )
            return False
    
    def log_operation(self, operation_type: str, filepath_old: str, 
                     filepath_new: str = None, status: str = 'success',
                     error_msg: str = None):
        """记录文件操作到数据库"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            filesize = os.path.getsize(filepath_old) if os.path.exists(filepath_old) else 0
            
            cur.execute("""
                INSERT INTO file_operation_log (
                    operation_type, filepath_old, filepath_new, filesize,
                    operated_by, status, error_msg
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                operation_type,
                filepath_old,
                filepath_new,
                filesize,
                'verify_structure_script',
                status,
                error_msg
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"记录操作日志失败: {e}")
    
    def process_new_uploads(self):
        """处理新上传的文件（确保每个文件只处理一次）"""
        new_uploads_dir = os.path.join(self.work_area, 'new_uploads')
        trash_bin_dir = os.path.join(self.work_area, 'trash_bin')
        
        if not os.path.exists(new_uploads_dir):
            logger.warning(f"目录不存在: {new_uploads_dir}")
            return
        
        # 加载元数据
        self.metadata = self.load_metadata()
        
        # 收集所有文件（去重）
        files_to_process = {}  # {filename: source_path}
        for root, dirs, files in os.walk(new_uploads_dir):
            for filename in files:
                # 跳过metadata_emergency.csv文件
                if filename == 'metadata_emergency.csv':
                    continue
                # 每个文件名只记录第一次出现的路径
                if filename not in files_to_process:
                    files_to_process[filename] = os.path.join(root, filename)
        
        # 处理每个文件（确保只处理一次）
        for filename, source_path in files_to_process.items():
            self.stats['total'] += 1
            
            try:
                # 验证文件名
                is_valid, error_msg = self.validate_filename(filename, 'alarm_image')
                
                if is_valid:
                    # 解析目标路径
                    path_info = self.parse_target_path(filename, os.path.dirname(source_path))
                    target_path = os.path.join(path_info['target_path'], filename)
                    
                    # 移动到正式库
                    if self.move_file(source_path, target_path, 'move'):
                        self.stats['valid'] += 1
                        self.stats['moved'] += 1
                        logger.info(f"✅ 合规文件已移动: {filename}")
                    else:
                        self.stats['errors'] += 1
                else:
                    # 不合规，移到垃圾箱
                    self.stats['invalid'] += 1
                    trash_path = os.path.join(trash_bin_dir, filename)
                    self.move_file(source_path, trash_path, 'delete')
                    logger.warning(f"⚠️ 不合规文件: {filename}, 原因: {error_msg}")
            
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"❌ 处理文件失败: {filename}, 错误: {e}")
    
    def print_summary(self):
        """打印处理摘要"""
        logger.info("=" * 60)
        logger.info("文件处理摘要")
        logger.info("=" * 60)
        logger.info(f"总文件数: {self.stats['total']}")
        logger.info(f"合规文件: {self.stats['valid']}")
        logger.info(f"不合规文件: {self.stats['invalid']}")
        logger.info(f"成功移动: {self.stats['moved']}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info("=" * 60)
    
    def run(self):
        """执行验证流程"""
        logger.info("🚀 开始文件规范检测...")
        
        try:
            self.process_new_uploads()
            self.print_summary()
            logger.info("✅ 文件规范检测完成！")
            
        except Exception as e:
            logger.error(f"❌ 执行失败: {e}")
            raise


def main():
    """主函数"""
    verifier = FileStructureVerifier()
    verifier.run()


if __name__ == '__main__':
    main()
