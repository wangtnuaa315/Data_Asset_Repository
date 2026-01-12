#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从CSV导入业务数据脚本
import_from_csv.py

功能：
1. 读取metadata_emergency.csv中的告警数据
2. 匹配对应的asset_id
3. 写入PostgreSQL的emergency_alarm_assets表
"""

import os
import csv
import logging
import psycopg2
from psycopg2.extras import Json
import yaml
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/data_asset/logs/import_from_csv.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CSVBusinessImporter:
    """从CSV导入业务数据"""
    
    def __init__(self, config_path='/opt/data_asset/config.yaml'):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.nas_base = self.config['nas']['base_path']
        self.pg_config = self.config['postgresql']
        
        # 统计信息
        self.stats = {
            'total_records': 0,
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def connect_pg(self):
        """连接PostgreSQL"""
        return psycopg2.connect(
            host=self.pg_config['host'],
            port=self.pg_config['port'],
            user=self.pg_config['user'],
            password=self.pg_config['password'],
            database=self.pg_config['database']
        )
    
    def find_asset_id(self, filename: str):
        """
        根据文件名查找asset_id
        
        Args:
            filename: 文件名，如 alarm_xxx.png
        
        Returns:
            asset_id或None
        """
        try:
            conn = self.connect_pg()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id FROM asset_catalog
                WHERE filename = %s
                  AND status = 'ready'
                LIMIT 1
            """, (filename,))
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                return result[0]
            else:
                logger.warning(f"未找到文件对应的资产: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"查询asset_id失败: {e}")
            return None
    
    def import_alarm_record(self, record: dict):
        """
        导入单条告警记录
        
        Args:
            record: CSV中的一行数据
        """
        try:
            filename = record['filename']
            
            # 查找对应的asset_id
            asset_id = self.find_asset_id(filename)
            if not asset_id:
                self.stats['skipped'] += 1
                logger.warning(f"跳过记录（未找到资产）: {filename}")
                return
            
            conn = self.connect_pg()
            cur = conn.cursor()
            
            # 解析告警时间
            alarm_time = None
            if record.get('alarm_time'):
                try:
                    from dateutil import parser
                    alarm_time = parser.parse(record['alarm_time'])
                except:
                    alarm_time = None
            
            # 插入告警记录
            cur.execute("""
                INSERT INTO emergency_alarm_assets (
                    asset_id,
                    alarm_name,
                    dev_code,
                    alarm_time,
                    analysis,
                    business_data,
                    created_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                asset_id,
                record.get('alarm_name', ''),
                record.get('device_code', ''),
                alarm_time,
                record.get('analysis_result', ''),
                Json({
                    'category': record.get('category', ''),
                    'alarm_id': record.get('alarm_id', ''),
                    'source': 'csv_import'
                })
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.stats['imported'] += 1
            logger.info(f"✅ 导入告警记录: {filename} - {record.get('alarm_name', '')}")
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ 导入失败: {filename}, 错误: {e}")
    
    def import_from_csv(self, csv_file: str):
        """
        从CSV文件导入所有告警记录
        
        Args:
            csv_file: CSV文件路径
        """
        if not os.path.exists(csv_file):
            logger.error(f"CSV文件不存在: {csv_file}")
            return
        
        logger.info(f"📋 开始从CSV导入: {csv_file}")
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    self.stats['total_records'] += 1
                    self.import_alarm_record(row)
            
            logger.info("✅ CSV导入完成！")
            
        except Exception as e:
            logger.error(f"读取CSV失败: {e}")
    
    def print_summary(self):
        """打印导入摘要"""
        logger.info("=" * 60)
        logger.info("业务数据导入摘要")
        logger.info("=" * 60)
        logger.info(f"CSV记录总数: {self.stats['total_records']}")
        logger.info(f"成功导入: {self.stats['imported']}")
        logger.info(f"跳过记录: {self.stats['skipped']}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info("=" * 60)
    
    def run(self, csv_file=None):
        """
        执行导入
        
        Args:
            csv_file: CSV文件路径，默认为new_uploads/metadata_emergency.csv
        """
        if not csv_file:
            csv_file = os.path.join(
                self.nas_base,
                '00_Work_Area',
                'new_uploads',
                'metadata_emergency.csv'
            )
        
        logger.info("🚀 开始业务数据导入...")
        
        try:
            self.import_from_csv(csv_file)
            self.print_summary()
            
        except Exception as e:
            logger.error(f"导入过程出错: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从CSV导入业务数据')
    parser.add_argument(
        '--csv',
        type=str,
        help='CSV文件路径（默认：trash_bin/metadata_emergency.csv）'
    )
    
    args = parser.parse_args()
    
    importer = CSVBusinessImporter()
    importer.run(csv_file=args.csv)


if __name__ == '__main__':
    main()
