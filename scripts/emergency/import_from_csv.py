#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从CSV导入业务数据脚本 (高性能版)
import_from_csv.py

功能：
1. 预加载所有资产文件名到内存 (避免逐条查询)
2. 批量扫描多个 CSV 文件
3. 批量 INSERT (每 500 条提交一次)
4. 进度条显示
"""

import os
import csv
import glob
import logging
import psycopg2
from psycopg2.extras import Json, execute_values
import yaml
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/data_asset/logs/import_from_csv.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CSVBusinessImporter:
    """从CSV导入业务数据 (高性能版)"""
    
    def __init__(self, config_path='/opt/data_asset/config.yaml'):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.nas_base = self.config['nas']['base_path']
        self.pg_config = self.config['postgresql']
        
        # 预加载的资产映射: filename -> asset_id
        self.asset_map = {}
        
        # 批量插入缓冲
        self.batch_size = 500
        self.insert_buffer = []
        
        # 统计信息
        self.stats = {
            'total_csv_rows': 0,
            'matched': 0,
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
    
    def preload_asset_map(self):
        """
        预加载所有资产文件名到内存
        这是性能优化的关键：避免每行都查询数据库
        """
        logger.info("📂 预加载资产文件名映射...")
        
        try:
            conn = self.connect_pg()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, filename FROM asset_catalog
                WHERE status = 'ready'
            """)
            
            rows = cur.fetchall()
            self.asset_map = {row[1]: row[0] for row in rows}
            
            cur.close()
            conn.close()
            
            logger.info(f"✅ 已加载 {len(self.asset_map)} 个资产文件名到内存")
            
        except Exception as e:
            logger.error(f"预加载资产映射失败: {e}")
            raise
    
    def flush_buffer(self, conn):
        """批量插入缓冲区的数据"""
        if not self.insert_buffer:
            return
        
        try:
            cur = conn.cursor()
            
            # 使用 execute_values 批量插入
            execute_values(
                cur,
                """
                INSERT INTO emergency_alarm_assets (
                    asset_id, alarm_name, dev_code, alarm_time, 
                    analysis, business_data, created_at, updated_at
                ) VALUES %s
                """,
                self.insert_buffer,
                template="(%s, %s, %s, %s, %s, %s, NOW(), NOW())"
            )
            
            conn.commit()
            cur.close()
            
            self.stats['imported'] += len(self.insert_buffer)
            self.insert_buffer = []
            
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            conn.rollback()
            self.stats['errors'] += len(self.insert_buffer)
            self.insert_buffer = []
    
    def process_row(self, row: dict, conn):
        """
        处理单行 CSV 数据
        使用内存映射快速判断是否匹配
        """
        filename = row.get('filename', '')
        
        # 在内存中快速查找 (O(1) 复杂度)
        asset_id = self.asset_map.get(filename)
        
        if not asset_id:
            # 无匹配，跳过（这是大多数情况）
            self.stats['skipped'] += 1
            return
        
        self.stats['matched'] += 1
        
        # 解析告警时间
        alarm_time = None
        if row.get('alarm_time'):
            try:
                from dateutil import parser
                alarm_time = parser.parse(row['alarm_time'])
            except:
                alarm_time = None
        
        # 添加到缓冲区
        self.insert_buffer.append((
            asset_id,
            row.get('alarm_name', ''),
            row.get('device_code', ''),
            alarm_time,
            row.get('analysis_result', ''),
            Json({
                'category': row.get('category', ''),
                'alarm_id': row.get('alarm_id', ''),
                'source': 'csv_import'
            })
        ))
        
        # 缓冲区满时批量插入
        if len(self.insert_buffer) >= self.batch_size:
            self.flush_buffer(conn)
    
    def import_from_csv(self, csv_file: str, conn):
        """
        从单个 CSV 文件导入
        """
        if not os.path.exists(csv_file):
            logger.error(f"CSV文件不存在: {csv_file}")
            return
        
        file_rows = 0
        file_matched = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    self.stats['total_csv_rows'] += 1
                    file_rows += 1
                    
                    old_matched = self.stats['matched']
                    self.process_row(row, conn)
                    if self.stats['matched'] > old_matched:
                        file_matched += 1
                    
                    # 每 10 万行显示进度
                    if file_rows % 100000 == 0:
                        logger.info(f"  ... 已扫描 {file_rows:,} 行, 匹配 {file_matched:,} 条")
            
            # 处理剩余缓冲
            self.flush_buffer(conn)
            
            logger.info(f"📄 文件完成: {file_rows:,} 行, 匹配 {file_matched:,} 条")
            
        except Exception as e:
            logger.error(f"读取CSV失败: {e}")
    
    def print_summary(self):
        """打印导入摘要"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 业务数据导入摘要")
        logger.info("=" * 60)
        logger.info(f"CSV 总行数:     {self.stats['total_csv_rows']:,}")
        logger.info(f"匹配资产数:     {self.stats['matched']:,}")
        logger.info(f"成功导入:       {self.stats['imported']:,}")
        logger.info(f"跳过 (无匹配):  {self.stats['skipped']:,}")
        logger.info(f"错误数:         {self.stats['errors']:,}")
        logger.info("=" * 60)
    
    def run(self, csv_file=None, csv_dir=None):
        """
        执行导入
        
        Args:
            csv_file: 单个CSV文件路径（可选）
            csv_dir: CSV文件目录，自动扫描所有.csv文件（可选）
        """
        logger.info("🚀 开始业务数据导入 (高性能版)...")
        start_time = datetime.now()
        
        # 1. 预加载资产映射
        self.preload_asset_map()
        
        if not self.asset_map:
            logger.warning("⚠️ 资产库为空，无法进行匹配")
            return
        
        # 2. 收集 CSV 文件
        csv_files = []
        
        if csv_file:
            csv_files = [csv_file]
        else:
            if not csv_dir:
                csv_dir = os.path.join(
                    self.nas_base,
                    '00_Work_Area',
                    'new_uploads'
                )
            
            if os.path.isdir(csv_dir):
                csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
                csv_files.sort()
                logger.info(f"📂 扫描目录: {csv_dir}")
                logger.info(f"📋 发现 {len(csv_files)} 个 CSV 文件")
            else:
                logger.error(f"目录不存在: {csv_dir}")
                return
        
        if not csv_files:
            logger.warning("⚠️ 未找到任何 CSV 文件")
            return
        
        # 3. 使用单个数据库连接处理所有文件
        try:
            conn = self.connect_pg()
            
            for idx, csv_path in enumerate(csv_files, 1):
                logger.info("")
                logger.info(f"{'='*60}")
                logger.info(f"📄 [{idx}/{len(csv_files)}] {os.path.basename(csv_path)}")
                logger.info(f"{'='*60}")
                self.import_from_csv(csv_path, conn)
            
            conn.close()
            
            # 4. 打印摘要
            self.print_summary()
            
            # 5. 显示耗时
            elapsed = datetime.now() - start_time
            logger.info(f"⏱️  总耗时: {elapsed}")
            
        except Exception as e:
            logger.error(f"导入过程出错: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从CSV导入业务数据 (高性能版)')
    parser.add_argument(
        '--csv',
        type=str,
        help='单个CSV文件路径'
    )
    parser.add_argument(
        '--dir',
        type=str,
        help='CSV文件目录（扫描所有.csv）'
    )
    
    args = parser.parse_args()
    
    importer = CSVBusinessImporter()
    importer.run(csv_file=args.csv, csv_dir=args.dir)


if __name__ == '__main__':
    main()
