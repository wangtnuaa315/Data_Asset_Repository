#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
match_images.py

图片匹配脚本：扫描上传的图片，从MySQL表中匹配元数据，生成metadata_emergency.csv

功能：
1. 扫描 new_uploads/ 目录中的图片文件
2. 支持解压 .zip 压缩包
3. 在 vp_ai_device_alarm 和 vp_hk_alarm 表中匹配图片
4. 检查PostgreSQL避免重复入库
5. 生成 metadata_emergency.csv 供后续脚本使用
"""

import os
import sys
import csv
import zipfile
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import yaml
import psycopg2

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emergency.data_source_manager import DataSourceManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/match_images.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ImageMatcher:
    """图片匹配器"""
    
    # 支持的图片格式
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    
    def __init__(self, config_path: str = None):
        """
        初始化图片匹配器
        
        Args:
            config_path: 全局配置文件路径
        """
        # 加载全局配置
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config.yaml'
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.global_config = yaml.safe_load(f)
        
        # 初始化数据源管理器
        self.ds_manager = DataSourceManager()
        
        # PostgreSQL连接（用于去重检查）
        self._pg_conn = None
        
        # 工作目录
        self.nas_path = self.global_config.get('nas_path', '/data/nas_data')
        self.work_area = os.path.join(self.nas_path, '00_Work_Area')
        self.new_uploads_dir = os.path.join(self.work_area, 'new_uploads')
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'matched': 0,
            'unmatched': 0,
            'skipped_duplicate': 0,
            'errors': 0
        }
    
    def connect_postgres(self):
        """连接PostgreSQL数据库"""
        if self._pg_conn is not None:
            return self._pg_conn
        
        pg_config = self.global_config.get('postgresql', {})
        self._pg_conn = psycopg2.connect(
            host=pg_config.get('host', 'localhost'),
            port=pg_config.get('port', 5432),
            user=pg_config.get('user', 'admin'),
            password=pg_config.get('password', ''),
            database=pg_config.get('database', 'asset_catalog')
        )
        return self._pg_conn
    
    def close_connections(self):
        """关闭所有数据库连接"""
        if self._pg_conn:
            self._pg_conn.close()
            self._pg_conn = None
        self.ds_manager.close_connection()
    
    def extract_zip_files(self) -> List[str]:
        """
        解压new_uploads目录中的zip文件
        
        Returns:
            解压出的图片文件列表
        """
        extracted_files = []
        
        for filename in os.listdir(self.new_uploads_dir):
            if filename.lower().endswith('.zip'):
                zip_path = os.path.join(self.new_uploads_dir, filename)
                logger.info(f"📦 解压: {filename}")
                
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        for member in zf.namelist():
                            # 只提取图片文件
                            ext = os.path.splitext(member)[1].lower()
                            if ext in self.SUPPORTED_EXTENSIONS:
                                # 提取到new_uploads目录
                                zf.extract(member, self.new_uploads_dir)
                                extracted_path = os.path.join(
                                    self.new_uploads_dir, member
                                )
                                extracted_files.append(extracted_path)
                                logger.debug(f"  ✓ 提取: {member}")
                    
                    # 解压成功后，可选择删除或移动zip文件
                    # os.remove(zip_path)
                    
                except zipfile.BadZipFile:
                    logger.error(f"❌ 无效的zip文件: {filename}")
                except Exception as e:
                    logger.error(f"❌ 解压失败 {filename}: {e}")
        
        return extracted_files
    
    def scan_image_files(self) -> List[str]:
        """
        扫描new_uploads目录中的图片文件
        
        Returns:
            图片文件路径列表
        """
        image_files = []
        
        for root, dirs, files in os.walk(self.new_uploads_dir):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    filepath = os.path.join(root, filename)
                    image_files.append(filepath)
        
        return image_files
    
    def is_already_registered(self, filename: str) -> bool:
        """
        检查文件是否已在PostgreSQL中注册
        
        Args:
            filename: 文件名
            
        Returns:
            True if already registered
        """
        try:
            conn = self.connect_postgres()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM asset_catalog WHERE filename = %s LIMIT 1",
                    (filename,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f"⚠️ 去重检查失败: {e}")
            return False
    
    def match_single_image(self, filepath: str) -> Optional[Dict]:
        """
        匹配单个图片文件
        
        Args:
            filepath: 图片文件路径
            
        Returns:
            匹配结果字典，未匹配返回None
        """
        filename = os.path.basename(filepath)
        
        # 检查是否已入库
        if self.is_already_registered(filename):
            logger.info(f"⏭️ 跳过已入库: {filename}")
            self.stats['skipped_duplicate'] += 1
            return None
        
        # 在所有数据源中匹配
        result = self.ds_manager.match_image_all_sources(filename)
        
        if result:
            # 构建目标路径
            alarm_name = result.get('alarm_name', '未分类')
            alarm_time = result.get('alarm_time')
            target_subpath = self.ds_manager.build_target_path(alarm_name, alarm_time)
            
            result['filename'] = filename
            result['source_path'] = filepath
            result['target_subpath'] = target_subpath
            result['source_table'] = result.get('_table', '')  # 记录来源表
            
            self.stats['matched'] += 1
            logger.info(f"✅ 匹配成功: {filename} → {target_subpath}")
        else:
            self.stats['unmatched'] += 1
            logger.warning(f"❓ 未匹配: {filename}")
        
        return result
    
    def generate_metadata_csv(
        self, 
        matched_results: List[Dict],
        output_path: str = None
    ) -> str:
        """
        生成metadata_emergency.csv文件
        
        Args:
            matched_results: 匹配结果列表
            output_path: 输出路径，默认为new_uploads/metadata_emergency.csv
            
        Returns:
            生成的CSV文件路径
        """
        if output_path is None:
            output_path = os.path.join(
                self.new_uploads_dir, 
                'metadata_emergency.csv'
            )
        
        # CSV字段
        fieldnames = [
            'filename',
            'alarm_name',
            'alarm_time',
            'device_code',
            'analysis',
            'source_table',
            'target_subpath'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for result in matched_results:
                # 格式化时间
                alarm_time = result.get('alarm_time')
                if alarm_time:
                    if isinstance(alarm_time, datetime):
                        result['alarm_time'] = alarm_time.strftime('%Y-%m-%d %H:%M:%S')
                
                writer.writerow(result)
        
        logger.info(f"📄 生成CSV: {output_path} ({len(matched_results)} 条记录)")
        return output_path
    
    def run(self, extract_zip: bool = True) -> str:
        """
        执行完整的匹配流程
        
        Args:
            extract_zip: 是否解压zip文件
            
        Returns:
            生成的metadata_emergency.csv路径
        """
        logger.info("🚀 开始图片匹配流程...")
        
        # 1. 解压zip文件
        if extract_zip:
            self.extract_zip_files()
        
        # 2. 扫描图片文件
        image_files = self.scan_image_files()
        self.stats['total_files'] = len(image_files)
        logger.info(f"📁 发现 {len(image_files)} 个图片文件")
        
        if not image_files:
            logger.warning("⚠️ 没有找到图片文件")
            return None
        
        # 3. 逐个匹配
        matched_results = []
        for filepath in image_files:
            try:
                result = self.match_single_image(filepath)
                if result:
                    matched_results.append(result)
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"❌ 处理失败 {filepath}: {e}")
        
        # 4. 生成CSV
        csv_path = None
        if matched_results:
            csv_path = self.generate_metadata_csv(matched_results)
        
        # 5. 输出统计
        logger.info("=" * 50)
        logger.info("📊 匹配统计:")
        logger.info(f"   总文件数: {self.stats['total_files']}")
        logger.info(f"   匹配成功: {self.stats['matched']}")
        logger.info(f"   未匹配:   {self.stats['unmatched']}")
        logger.info(f"   已入库跳过: {self.stats['skipped_duplicate']}")
        logger.info(f"   处理错误: {self.stats['errors']}")
        logger.info("=" * 50)
        
        # 6. 关闭连接
        self.close_connections()
        
        return csv_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='图片匹配脚本 - 从MySQL表中匹配上传图片的元数据'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='全局配置文件路径'
    )
    parser.add_argument(
        '--no-extract',
        action='store_true',
        help='不解压zip文件'
    )
    
    args = parser.parse_args()
    
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 执行匹配
    matcher = ImageMatcher(config_path=args.config)
    csv_path = matcher.run(extract_zip=not args.no_extract)
    
    if csv_path:
        print(f"\n✅ 匹配完成，生成: {csv_path}")
        print("下一步: python scripts/emergency/verify_structure.py")
    else:
        print("\n⚠️ 没有匹配到任何图片")


if __name__ == '__main__':
    main()
