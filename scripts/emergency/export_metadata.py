#!/usr/bin/env python3
"""
元数据导出脚本 - 支持多场景
export_metadata.py

功能：
1. 从MySQL业务库导出告警数据
2. 提取真实的图片文件名（从JSON或字段）
3. 生成metadata_emergency.csv供文件分类使用
4. 支持多种业务场景配置
"""

import pymysql
import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
import yaml

# 场景配置
SCENARIOS = {
    # 场景1：应急二次分析（海康告警）
    'emergency_hk_alarm': {
        'table': 'vp_hk_alarm',
        'description': '应急海康设备告警（二次分析）',
        'query': """
            SELECT 
                ID,
                ALARM_NAME,
                ALARM_TIME,
                DEV_CODE,
                img2,
                analysis,
                analysis_result
            FROM vp_hk_alarm
            WHERE analysis_result = 0  -- 只要准确的告警
              AND ALARM_TIME >= %s
            ORDER BY ALARM_TIME DESC
        """,
        'filename_extractor': 'extract_from_img2',  # 文件名提取方法
    },
    
    # 场景2：应急AI设备告警
    'emergency_ai_alarm': {
        'table': 'vp_ai_device_alarm',
        'description': '应急AI设备告警',
        'query': """
            SELECT 
                ID,
                ALARM_NAME,
                ALARM_TIME,
                DEV_CODE,
                ALARM_IMG,
                analysis
            FROM vp_ai_device_alarm
            WHERE ALARM_TIME >= %s
            ORDER BY ALARM_TIME DESC
        """,
        'filename_extractor': 'extract_from_alarm_img',
    },
}


class MetadataExporter:
    """元数据导出器"""
    
    def __init__(self, config_path='/opt/data_asset/config.yaml'):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.mysql_config = self.config['mysql']
    
    def connect_mysql(self):
        """连接MySQL"""
        return pymysql.connect(
            host=self.mysql_config['host'],
            user=self.mysql_config['user'],
            password=self.mysql_config['password'],
            database=self.mysql_config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def extract_from_img2(self, row: dict) -> str:
        """
        从img2字段提取文件名
        
        img2可能的格式：
        - 完整路径: /hkEvent/2025_12/abc123.png
        - 文件名: abc123.png
        """
        img2 = row.get('img2', '')
        
        if not img2:
            # 如果img2为空，尝试从analysis中提取
            return self.extract_from_analysis(row)
        
        # 提取文件名
        filename = os.path.basename(img2)
        
        # 确保格式为 alarm_xxx.png
        if not filename.startswith('alarm_'):
            # 如果原文件名不是alarm_开头，重命名
            name_part = Path(filename).stem
            ext = Path(filename).suffix or '.png'
            filename = f"alarm_{name_part}{ext}"
        
        return filename
    
    def extract_from_analysis(self, row: dict) -> str:
        """
        从analysis JSON字段提取文件名
        
        analysis可能的格式：
        {
            "img_url": "http://xxx/abc123.png",
            "result": "误报",
            ...
        }
        """
        analysis_str = row.get('analysis', '{}')
        
        try:
            analysis = json.loads(analysis_str) if isinstance(analysis_str, str) else analysis_str
            
            # 尝试从不同的字段提取URL或文件名
            for field in ['img_url', 'image_url', 'img', 'image', 'file']:
                if field in analysis:
                    url = analysis[field]
                    filename = os.path.basename(url)
                    
                    if not filename.startswith('alarm_'):
                        name_part = Path(filename).stem
                        ext = Path(filename).suffix or '.png'
                        filename = f"alarm_{name_part}{ext}"
                    
                    return filename
        except:
            pass
        
        # 如果都提取失败，使用设备编码
        dev_code = row.get('DEV_CODE', row.get('dev_code', 'unknown'))
        return f"alarm_{dev_code}.png"
    
    def extract_from_alarm_img(self, row: dict) -> str:
        """从ALARM_IMG字段提取文件名"""
        alarm_img = row.get('ALARM_IMG', '')
        
        if not alarm_img:
            return self.extract_from_analysis(row)
        
        filename = os.path.basename(alarm_img)
        
        if not filename.startswith('alarm_'):
            name_part = Path(filename).stem
            ext = Path(filename).suffix or '.png'
            filename = f"alarm_{name_part}{ext}"
        
        return filename
    
    def extract_analysis_result(self, row: dict) -> str:
        """提取分析结果信息"""
        analysis_str = row.get('analysis', '{}')
        
        try:
            analysis = json.loads(analysis_str) if isinstance(analysis_str, str) else analysis_str
            result = analysis.get('result', '')
            return str(result)
        except:
            return ''
    
    def export_scenario(self, scenario_name: str, start_date: str, output_file: str):
        """
        导出指定场景的元数据
        
        Args:
            scenario_name: 场景名称，如 'emergency_hk_alarm'
            start_date: 开始日期，如 '2025-12-01'
            output_file: 输出CSV文件路径
        """
        if scenario_name not in SCENARIOS:
            raise ValueError(f"未知场景: {scenario_name}，可用场景: {list(SCENARIOS.keys())}")
        
        scenario = SCENARIOS[scenario_name]
        print(f"📋 导出场景: {scenario['description']}")
        print(f"📅 起始日期: {start_date}")
        
        # 连接MySQL
        conn = self.connect_mysql()
        cursor = conn.cursor()
        
        try:
            # 执行查询
            cursor.execute(scenario['query'], (start_date,))
            rows = cursor.fetchall()
            
            print(f"✅ 查询到 {len(rows)} 条记录")
            
            # 获取文件名提取方法
            extractor_method = getattr(self, scenario['filename_extractor'])
            
            # 写入CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['filename', 'alarm_name', 'analysis_result', 'alarm_time', 'device_code'])
                
                for row in rows:
                    filename = extractor_method(row)
                    alarm_name = row.get('ALARM_NAME', row.get('alarm_name', '未分类'))
                    analysis_result = self.extract_analysis_result(row)
                    alarm_time = row.get('ALARM_TIME', row.get('alarm_time', ''))
                    device_code = row.get('DEV_CODE', row.get('dev_code', ''))
                    
                    # 格式化时间
                    if isinstance(alarm_time, datetime):
                        alarm_time = alarm_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    writer.writerow([
                        filename,
                        alarm_name,
                        analysis_result,
                        str(alarm_time),
                        device_code
                    ])
            
            print(f"✅ 已导出到: {output_file}")
            
        finally:
            cursor.close()
            conn.close()
    
    def list_scenarios(self):
        """列出所有可用场景"""
        print("可用的导出场景：")
        print("=" * 60)
        for name, config in SCENARIOS.items():
            print(f"场景名称: {name}")
            print(f"  描述: {config['description']}")
            print(f"  数据表: {config['table']}")
            print(f"  提取方法: {config['filename_extractor']}")
            print()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='元数据导出工具')
    parser.add_argument('--scenario', type=str, 
                       help='场景名称（如 emergency_hk_alarm）')
    parser.add_argument('--start-date', type=str, 
                       default='2025-12-01',
                       help='起始日期（默认 2025-12-01）')
    parser.add_argument('--output', type=str, 
                       default='metadata_emergency.csv',
                       help='输出文件路径（默认 metadata_emergency.csv）')
    parser.add_argument('--list', action='store_true',
                       help='列出所有可用场景')
    
    args = parser.parse_args()
    
    exporter = MetadataExporter()
    
    if args.list:
        exporter.list_scenarios()
        return
    
    if not args.scenario:
        print("错误：请指定场景名称（使用 --scenario）")
        print("运行 --list 查看所有可用场景")
        return
    
    exporter.export_scenario(args.scenario, args.start_date, args.output)


if __name__ == '__main__':
    main()
