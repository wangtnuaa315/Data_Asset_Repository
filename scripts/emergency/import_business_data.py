#!/usr/bin/env python3
"""
业务数据导入脚本
import_business_data.py

功能：
1. 从MySQL读取告警业务数据（vp_ai_device_alarm, vp_hk_alarm）
2. 匹配对应的图片资产
3. 写入PostgreSQL的emergency_alarm_assets表
4. 支持增量导入和全量导入
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import Json
import pymysql
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/data_asset/logs/import_business.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BusinessDataImporter:
    """业务数据导入器"""
    
    def __init__(self, config_path='/opt/data_asset/config.yaml'):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # MySQL配置
        self.mysql_config = self.config['mysql']
        
        # PostgreSQL配置
        self.pg_config = self.config['postgresql']
        
        # 统计信息
        self.stats = {
            'total': 0,
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def connect_mysql(self):
        """连接MySQL（如果启用）"""
        if not self.mysql_config.get('enabled', True):
            raise Exception("MySQL未启用，请在config.yaml中设置 mysql.enabled=true")
        
        return pymysql.connect(
            host=self.mysql_config['host'],
            user=self.mysql_config['user'],
            password=self.mysql_config['password'],
            database=self.mysql_config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def connect_pg(self):
        """连接PostgreSQL"""
        return psycopg2.connect(
            host=self.pg_config['host'],
            port=self.pg_config['port'],
            user=self.pg_config['user'],
            password=self.pg_config['password'],
            database=self.pg_config['database']
        )
    
    def find_asset_by_path(self, img_path: str) -> Optional[int]:
        """
        根据图片路径查找对应的asset_id
        
        Args:
            img_path: MySQL中的ALARM_IMG路径，如 /hkEvent/2025_12/xxx.png
        
        Returns:
            asset_id或None
        """
        try:
            conn = self.connect_pg()
            cur = conn.cursor()
            
            # 方案1：通过文件名模糊匹配
            filename = os.path.basename(img_path)
            
            cur.execute("""
                SELECT id FROM asset_catalog
                WHERE filename = %s
                  AND status = 'ready'
                LIMIT 1
            """, (filename,))
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"查找资产失败: {img_path}, 错误: {e}")
            return None
    
    def import_ai_device_alarm(self, alarm: Dict) -> bool:
        """导入AI设备告警"""
        try:
            # 查找对应的图片资产
            img_path = alarm.get('ALARM_IMG')
            if not img_path:
                logger.warning(f"告警 {alarm['ID']} 没有图片")
                self.stats['skipped'] += 1
                return False
            
            asset_id = self.find_asset_by_path(img_path)
            if not asset_id:
                logger.warning(f"找不到对应的资产: {img_path}")
                self.stats['skipped'] += 1
                return False
            
            # 构建business_data
            business_data = {
                'dev_code': alarm.get('DEV_CODE'),
                'dev_name': alarm.get('DEV_NAME'),
                'alarm_name': alarm.get('ALARM_NAME'),
                'channel_code': alarm.get('CHANNEL_CODE'),
                'channel_name': alarm.get('CHANNEL_NAME'),
                'area_name': alarm.get('AREA_CODE'),  # 注意：这里可能需要查询获取area_name
                'process_user_id': alarm.get('PROCESS_USER_ID'),
                'process_user_name': alarm.get('PROCESS_USER_NAME'),
                'process_time': str(alarm.get('PROCESS_TIME')) if alarm.get('PROCESS_TIME') else None,
                'source': alarm.get('source'),
                'level': alarm.get('LEVEL'),
                'analysis': alarm.get('analysis'),
                'analysis_time': str(alarm.get('analysis_time')) if alarm.get('analysis_time') else None,
                'link_screen': alarm.get('link_screen'),
                'link_live': alarm.get('link_live'),
                'link_capture': alarm.get('link_capture'),
                'link_record_type': alarm.get('link_record_type'),
                'img_original_name': alarm.get('img_original_name'),
                'video_record_id': alarm.get('VIDEO_RECORD_ID')
            }
            
            # 写入PostgreSQL
            conn = self.connect_pg()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO emergency_alarm_assets (
                    asset_id, alarm_id, alarm_type, alarm_time, area_code, status,
                    alarm_source, business_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                asset_id,
                alarm['ID'],
                alarm.get('ALARM_TYPE'),
                alarm.get('ALARM_TIME'),
                alarm.get('AREA_CODE'),
                alarm.get('STATUS', 1),
                'ai_device',
                Json(business_data)
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.stats['imported'] += 1
            logger.debug(f"✅ 导入AI设备告警: {alarm['ID']}")
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ 导入AI设备告警失败: {alarm.get('ID')}, 错误: {e}")
            return False
    
    def import_hk_alarm(self, alarm: Dict) -> bool:
        """导入海康设备告警"""
        try:
            # 查找对应的图片资产
            img_path = alarm.get('ALARM_IMG')
            if not img_path:
                logger.warning(f"告警 {alarm['ID']} 没有图片")
                self.stats['skipped'] += 1
                return False
            
            asset_id = self.find_asset_by_path(img_path)
            if not asset_id:
                logger.warning(f"找不到对应的资产: {img_path}")
                self.stats['skipped'] += 1
                return False
            
            # 构建business_data（包含海康特有字段）
            business_data = {
                'dev_code': alarm.get('DEV_CODE'),
                'dev_name': alarm.get('DEV_NAME'),
                'alarm_name': alarm.get('ALARM_NAME'),
                'channel_code': alarm.get('CHANNEL_CODE'),
                'channel_name': alarm.get('CHANNEL_NAME'),
                'area_name': alarm.get('AREA_CODE'),
                'process_user_id': alarm.get('PROCESS_USER_ID'),
                'process_user_name': alarm.get('PROCESS_USER_NAME'),
                'process_time': str(alarm.get('PROCESS_TIME')) if alarm.get('PROCESS_TIME') else None,
                'source': alarm.get('source'),
                'level': alarm.get('LEVEL'),
                # 海康特有字段
                'ext1': alarm.get('ext1'),
                'ext_detail': alarm.get('ext_detail'),
                'img2': alarm.get('img2'),
                'analysis': alarm.get('analysis'),
                'analysis_time': str(alarm.get('analysis_time')) if alarm.get('analysis_time') else None,
                'analysis_result': alarm.get('analysis_result'),
                'manual_review': alarm.get('manual_review'),
                'review_comments': alarm.get('review_comments'),
                'same_img': alarm.get('same_img'),
                'video_record_id': alarm.get('VIDEO_RECORD_ID')
            }
            
            # 写入PostgreSQL
            conn = self.connect_pg()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO emergency_alarm_assets (
                    asset_id, alarm_id, alarm_type, alarm_time, area_code, status,
                    alarm_source, business_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                asset_id,
                alarm['ID'],
                alarm.get('ALARM_TYPE'),
                alarm.get('ALARM_TIME'),
                alarm.get('AREA_CODE'),
                alarm.get('STATUS', 1),
                'hk_device',
                Json(business_data)
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.stats['imported'] += 1
            logger.debug(f"✅ 导入海康告警: {alarm['ID']}")
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ 导入海康告警失败: {alarm.get('ID')}, 错误: {e}")
            return False
    
    def import_alarms(self, table_name: str, alarm_source: str, 
                     start_date: Optional[str] = None):
        """
        导入告警数据
        
        Args:
            table_name: MySQL表名 (vp_ai_device_alarm 或 vp_hk_alarm)
            alarm_source: 告警来源 ('ai_device' 或 'hk_device')
            start_date: 开始日期，如 '2024-01-01'（支持增量导入）
        """
        logger.info(f"🔍 开始导入 {table_name} 数据...")
        
        try:
            # 连接MySQL
            mysql_conn = self.connect_mysql()
            cur = mysql_conn.cursor()
            
            # 构建查询条件
            where_clause = "WHERE 1=1"
            if start_date:
                where_clause += f" AND ALARM_TIME >= '{start_date}'"
            
            # 查询数据
            query = f"SELECT * FROM {table_name} {where_clause} ORDER BY ID"
            cur.execute(query)
            
            alarms = cur.fetchall()
            self.stats['total'] += len(alarms)
            
            logger.info(f"找到 {len(alarms)} 条记录")
            
            # 导入data
            for idx, alarm in enumerate(alarms, 1):
                if alarm_source == 'ai_device':
                    self.import_ai_device_alarm(alarm)
                else:
                    self.import_hk_alarm(alarm)
                
                # 每100条输出一次进度
                if idx % 100 == 0:
                    logger.info(f"进度: {idx}/{len(alarms)}")
            
            cur.close()
            mysql_conn.close()
            
        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            raise
    
    def print_summary(self):
        """打印导入摘要"""
        logger.info("=" * 60)
        logger.info("业务数据导入摘要")
        logger.info("=" * 60)
        logger.info(f"总记录数: {self.stats['total']}")
        logger.info(f"成功导入: {self.stats['imported']}")
        logger.info(f"跳过记录: {self.stats['skipped']}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info("=" * 60)
    
    def run(self, mode='incremental', days=7):
        """
        执行导入
        
        Args:
            mode: 'full' 全量导入, 'incremental' 增量导入
            days: 增量导入的天数
        """
        logger.info("🚀 开始业务数据导入...")
        
        try:
            # 计算开始日期
            start_date = None
            if mode == 'incremental':
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                logger.info(f"📅 增量导入，起始日期: {start_date}")
            
            # 导入AI设备告警
            self.import_alarms('vp_ai_device_alarm', 'ai_device', start_date)
            
            # 导入海康设备告警
            self.import_alarms('vp_hk_alarm', 'hk_device', start_date)
            
            # 打印摘要
            self.print_summary()
            
            logger.info("✅ 业务数据导入完成！")
            
        except Exception as e:
            logger.error(f"❌ 业务数据导入失败: {e}")
            raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='业务数据导入脚本')
    parser.add_argument('--mode', choices=['full', 'incremental'], 
                       default='incremental', help='导入模式')
    parser.add_argument('--days', type=int, default=7, 
                       help='增量导入的天数')
    
    args = parser.parse_args()
    
    importer = BusinessDataImporter()
    importer.run(mode=args.mode, days=args.days)


if __name__ == '__main__':
    main()
