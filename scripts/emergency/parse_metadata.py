#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_metadata.py

多格式元数据解析器：支持CSV和Excel格式，自动识别表来源

功能：
1. 解压上传的zip压缩包，扁平化提取图片到工作目录
2. 读取现场导出的表数据（CSV或Excel格式）
3. 自动识别数据来源表（vp_ai_device_alarm / vp_hk_alarm）
4. 根据图片文件名匹配元数据
5. 生成统一的metadata_emergency.csv供后续脚本使用
"""

import os
import sys
import csv
import zipfile
import shutil
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetadataParser:
    """多格式元数据解析器"""
    
    # 支持的图片格式
    SUPPORTED_IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    
    def __init__(self, work_dir: str, config_path: str = None):
        """
        初始化解析器
        
        Args:
            work_dir: 工作目录（包含图片和表数据文件）
            config_path: 字段映射配置文件路径，默认为同目录下config/field_mapping.yaml
        """
        self.work_dir = work_dir
        self.metadata_records = {}  # {filename: record}
        
        # 加载字段映射配置
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                'config',
                'field_mapping.yaml'
            )
        self.config = self._load_config(config_path)
        self.table_configs = self._build_table_configs()
    
    def _load_config(self, config_path: str) -> dict:
        """加载YAML配置文件"""
        try:
            import yaml
        except ImportError:
            logger.error("❌ 请安装 pyyaml: pip install pyyaml")
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"⚠️ 配置文件不存在: {config_path}，使用默认配置")
            return {}
    
    def _build_table_configs(self) -> dict:
        """从配置构建表字段映射"""
        tables = self.config.get('tables', {})
        configs = {}
        
        for table_name, table_config in tables.items():
            if not table_config.get('enabled', True):
                continue
            
            core = table_config.get('core_fields', {})
            configs[table_name] = {
                'image_field': core.get('image_path', 'ALARM_IMG'),
                'alarm_name_field': core.get('alarm_name', 'ALARM_NAME'),
                'alarm_time_field': core.get('alarm_time', 'ALARM_TIME'),
                'device_code_field': core.get('device_code', 'DEV_CODE'),
                'analysis_field': core.get('analysis', 'analysis'),
                'alarm_type_field': core.get('alarm_type', 'ALARM_TYPE'),
                'alarm_id_field': core.get('alarm_id', 'ID'),
                'area_code_field': core.get('area_code', 'AREA_CODE'),
                'status_field': core.get('status', 'STATUS'),
                'identifier_fields': table_config.get('identifier_fields', []),
                'extra_fields': table_config.get('extra_fields', []),
            }
        
        # 如果配置为空，使用默认配置
        if not configs:
            configs = {
                'vp_ai_device_alarm': {
                    'image_field': 'ALARM_IMG',
                    'alarm_name_field': 'ALARM_NAME',
                    'alarm_time_field': 'ALARM_TIME',
                    'device_code_field': 'DEV_CODE',
                    'analysis_field': 'analysis',
                    'identifier_fields': ['img_original_name'],
                },
                'vp_hk_alarm': {
                    'image_field': 'ALARM_IMG',
                    'alarm_name_field': 'ALARM_NAME',
                    'alarm_time_field': 'ALARM_TIME',
                    'device_code_field': 'DEV_CODE',
                    'analysis_field': 'analysis',
                    'identifier_fields': ['img2', 'same_img'],
                }
            }
        
        return configs
    
    def extract_zip_files(self) -> int:
        """
        解压工作目录中的所有zip文件，扁平化提取图片
        
        处理逻辑：
        - 遍历zip内所有文件
        - 只提取图片文件（忽略目录层级）
        - 图片提取到工作目录根层级
        - 处理文件名冲突
        
        Returns:
            提取的图片数量
        """
        extracted_count = 0
        zip_files = []
        
        for filename in os.listdir(self.work_dir):
            if filename.lower().endswith('.zip'):
                zip_files.append(os.path.join(self.work_dir, filename))
        
        if not zip_files:
            return 0
        
        logger.info(f"📦 发现 {len(zip_files)} 个压缩包")
        
        for zip_path in zip_files:
            zip_name = os.path.basename(zip_path)
            logger.info(f"  解压: {zip_name}")
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    for member in zf.namelist():
                        # 跳过目录
                        if member.endswith('/'):
                            continue
                        
                        # 获取文件名（忽略路径）
                        filename = os.path.basename(member)
                        if not filename:
                            continue
                        
                        # 检查是否为图片或表数据文件
                        ext = os.path.splitext(filename)[1].lower()
                        if ext not in self.SUPPORTED_IMAGE_EXT and ext not in ['.csv', '.xlsx', '.xls']:
                            continue
                        
                        # 目标路径（扁平化到工作目录）
                        target_path = os.path.join(self.work_dir, filename)
                        
                        # 处理文件名冲突
                        if os.path.exists(target_path):
                            base, extension = os.path.splitext(filename)
                            counter = 1
                            while os.path.exists(target_path):
                                target_path = os.path.join(
                                    self.work_dir, 
                                    f"{base}_{counter}{extension}"
                                )
                                counter += 1
                            filename = os.path.basename(target_path)
                        
                        # 提取文件
                        with zf.open(member) as src, open(target_path, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        
                        if ext in self.SUPPORTED_IMAGE_EXT:
                            extracted_count += 1
                
                logger.info(f"  ✅ 完成: {zip_name}")
                
            except zipfile.BadZipFile:
                logger.error(f"  ❌ 无效的zip文件: {zip_name}")
            except Exception as e:
                logger.error(f"  ❌ 解压失败 {zip_name}: {e}")
        
        logger.info(f"📷 共提取 {extracted_count} 个图片文件")
        return extracted_count
        
    def read_csv(self, filepath: str) -> List[Dict]:
        """读取CSV文件"""
        records = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            logger.info(f"✅ 读取CSV: {filepath} ({len(records)} 条)")
        except UnicodeDecodeError:
            # 尝试GBK编码
            with open(filepath, 'r', encoding='gbk') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            logger.info(f"✅ 读取CSV(GBK): {filepath} ({len(records)} 条)")
        return records
    
    def read_excel(self, filepath: str) -> List[Dict]:
        """读取Excel文件"""
        try:
            import openpyxl
        except ImportError:
            logger.error("❌ 请安装 openpyxl: pip install openpyxl")
            return []
        
        records = []
        wb = openpyxl.load_workbook(filepath, read_only=True)
        sheet = wb.active
        
        # 获取表头
        headers = [cell.value for cell in sheet[1]]
        
        # 读取数据行
        for row in sheet.iter_rows(min_row=2, values_only=True):
            record = dict(zip(headers, row))
            records.append(record)
        
        wb.close()
        logger.info(f"✅ 读取Excel: {filepath} ({len(records)} 条)")
        return records
    
    def detect_table_source(self, records: List[Dict], filename: str) -> str:
        """
        检测数据来源表
        
        Args:
            records: 数据记录列表
            filename: 文件名（可能包含表名信息）
            
        Returns:
            表名
        """
        # 先从文件名判断
        filename_lower = filename.lower()
        if 'ai_device' in filename_lower or 'ai告警' in filename_lower:
            return 'vp_ai_device_alarm'
        if 'hk_alarm' in filename_lower or '海康' in filename_lower:
            return 'vp_hk_alarm'
        
        # 从字段判断
        if records:
            sample = records[0]
            for table_name, config in self.table_configs.items():
                for field in config['identifier_fields']:
                    if field in sample:
                        return table_name
        
        # 默认返回第一个
        logger.warning(f"⚠️ 无法自动识别表来源，默认使用 vp_ai_device_alarm")
        return 'vp_ai_device_alarm'
    
    def extract_filename_from_path(self, path: str) -> str:
        """从路径中提取文件名"""
        if not path:
            return ''
        # 去除引号
        path = path.strip('"').strip("'")
        # 处理各种路径格式
        path = path.replace('\\', '/')
        return os.path.basename(path)
    
    def load_table_data(self, filepath: str) -> None:
        """
        加载表数据文件
        
        Args:
            filepath: CSV或Excel文件路径
        """
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.csv':
            records = self.read_csv(filepath)
        elif ext in ['.xlsx', '.xls']:
            records = self.read_excel(filepath)
        else:
            logger.warning(f"⚠️ 不支持的格式: {ext}")
            return
        
        if not records:
            return
        
        # 检测表来源
        filename = os.path.basename(filepath)
        source_table = self.detect_table_source(records, filename)
        config = self.table_configs[source_table]
        
        # 处理每条记录 - 检查多个图片字段
        # 图片可能在 ALARM_IMG、img2、same_img 等字段中
        image_fields = [
            config['image_field'],  # ALARM_IMG
            'img2',
            'same_img'
        ]
        
        for record in records:
            # 构建基础元数据
            metadata = {
                'alarm_name': record.get(config['alarm_name_field'], ''),
                'alarm_time': record.get(config['alarm_time_field'], ''),
                'device_code': record.get(config['device_code_field'], ''),
                'analysis': record.get(config['analysis_field'], ''),
                'source_table': source_table,
            }
            
            # 检查每个图片字段
            for field in image_fields:
                image_path = record.get(field, '')
                if not image_path:
                    continue
                    
                image_filename = self.extract_filename_from_path(image_path)
                if not image_filename:
                    continue
                
                # 添加到记录（如果还未存在）
                if image_filename not in self.metadata_records:
                    self.metadata_records[image_filename] = {
                        'filename': image_filename,
                        **metadata
                    }
        
        logger.info(f"📊 已加载 {len(records)} 条记录，来源表: {source_table}")
    
    def scan_and_load_all(self) -> None:
        """扫描工作目录并加载所有表数据文件"""
        for filename in os.listdir(self.work_dir):
            filepath = os.path.join(self.work_dir, filename)
            if not os.path.isfile(filepath):
                continue
            
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.csv', '.xlsx', '.xls']:
                # 跳过已生成的metadata_emergency.csv
                if filename == 'metadata_emergency.csv':
                    continue
                self.load_table_data(filepath)
    
    def match_images(self) -> List[Dict]:
        """
        匹配工作目录中的图片文件与元数据
        
        Returns:
            匹配成功的元数据列表
        """
        matched = []
        unmatched = []
        
        for filename in os.listdir(self.work_dir):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.SUPPORTED_IMAGE_EXT:
                continue
            
            if filename in self.metadata_records:
                matched.append(self.metadata_records[filename])
            else:
                unmatched.append(filename)
        
        logger.info(f"✅ 匹配成功: {len(matched)} 个")
        if unmatched:
            logger.warning(f"❓ 未匹配: {len(unmatched)} 个")
            for f in unmatched[:5]:
                logger.warning(f"   - {f}")
            if len(unmatched) > 5:
                logger.warning(f"   ... 及其他 {len(unmatched) - 5} 个")
        
        return matched
    
    def generate_metadata_csv(self, output_path: str = None) -> str:
        """
        生成统一的metadata_emergency.csv
        
        Args:
            output_path: 输出路径，默认为工作目录下
            
        Returns:
            生成的CSV文件路径
        """
        if output_path is None:
            output_path = os.path.join(self.work_dir, 'metadata_emergency.csv')
        
        matched = self.match_images()
        
        if not matched:
            logger.warning("⚠️ 没有匹配到任何图片")
            return None
        
        fieldnames = [
            'filename', 'alarm_name', 'alarm_time', 
            'device_code', 'analysis', 'source_table'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matched)
        
        logger.info(f"📄 生成: {output_path} ({len(matched)} 条)")
        return output_path
    
    def run(self) -> str:
        """执行完整流程"""
        logger.info(f"🚀 开始解析元数据，工作目录: {self.work_dir}")
        
        # 1. 解压压缩包（如有）
        self.extract_zip_files()
        
        # 2. 扫描并加载所有表数据
        self.scan_and_load_all()
        
        if not self.metadata_records:
            logger.error("❌ 未找到任何表数据文件（CSV/Excel）")
            return None
        
        # 3. 生成统一的CSV
        return self.generate_metadata_csv()


def main():
    parser = argparse.ArgumentParser(
        description='多格式元数据解析器 - 支持CSV/Excel'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='/data/nas_data/00_Work_Area/new_uploads',
        help='工作目录（默认: new_uploads）'
    )
    
    args = parser.parse_args()
    
    parser_obj = MetadataParser(args.dir)
    result = parser_obj.run()
    
    if result:
        print(f"\n✅ 元数据解析完成: {result}")
        print("下一步: python scripts/emergency/verify_structure.py")
    else:
        print("\n❌ 解析失败，请检查工作目录中的数据文件")


if __name__ == '__main__':
    main()
