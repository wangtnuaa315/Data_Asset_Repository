#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_source_manager.py

数据源管理模块，提供统一的多表数据访问接口
"""

import os
import yaml
import pymysql
from typing import Dict, List, Optional, Any
from pathlib import Path


class DataSourceManager:
    """数据源管理器，统一管理多表配置和查询"""
    
    def __init__(self, config_path: str = None):
        """
        初始化数据源管理器
        
        Args:
            config_path: 配置文件路径，默认为同目录下的config/data_sources.yaml
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                'config',
                'data_sources.yaml'
            )
        
        self.config_path = config_path
        self.config = self._load_config()
        self._connection = None
    
    def _load_config(self) -> Dict:
        """加载YAML配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_mysql_config(self) -> Dict:
        """获取MySQL连接配置"""
        return self.config.get('mysql', {})
    
    def get_data_sources(self) -> Dict:
        """获取所有数据源配置"""
        return self.config.get('data_sources', {})
    
    def get_enabled_sources(self) -> Dict:
        """获取所有启用的数据源"""
        sources = self.get_data_sources()
        return {k: v for k, v in sources.items() if v.get('enabled', True)}
    
    def get_target_directory(self) -> Dict:
        """获取目标目录配置"""
        return self.config.get('target_directory', {})
    
    def connect_mysql(self) -> pymysql.Connection:
        """建立MySQL连接"""
        if self._connection is not None:
            return self._connection
        
        mysql_config = self.get_mysql_config()
        self._connection = pymysql.connect(
            host=mysql_config.get('host', 'localhost'),
            port=mysql_config.get('port', 3306),
            user=mysql_config.get('user', 'root'),
            password=mysql_config.get('password', ''),
            database=mysql_config.get('database', ''),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return self._connection
    
    def close_connection(self):
        """关闭MySQL连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def match_image_in_source(
        self, 
        source_name: str, 
        filename: str
    ) -> Optional[Dict]:
        """
        在指定数据源中匹配图片
        
        Args:
            source_name: 数据源名称（如 'ai_device_alarm'）
            filename: 图片文件名
            
        Returns:
            匹配到的记录字典，未找到返回None
        """
        sources = self.get_data_sources()
        if source_name not in sources:
            return None
        
        source = sources[source_name]
        table = source['table']
        fields = source['fields']
        image_field = fields.get('image_path', 'ALARM_IMG')
        
        # 构建查询字段列表
        select_fields = []
        for key, db_field in fields.items():
            if db_field:
                select_fields.append(f"`{db_field}` AS `{key}`")
        
        # 添加扩展字段
        extra_fields = source.get('extra_fields', [])
        for field in extra_fields:
            select_fields.append(f"`{field}`")
        
        select_clause = ', '.join(select_fields)
        
        # 执行查询
        conn = self.connect_mysql()
        with conn.cursor() as cursor:
            sql = f"""
                SELECT {select_clause}
                FROM `{table}`
                WHERE `{image_field}` LIKE %s
                LIMIT 1
            """
            cursor.execute(sql, (f'%{filename}',))
            result = cursor.fetchone()
        
        if result:
            result['_source'] = source_name
            result['_table'] = table
        
        return result
    
    def match_image_all_sources(self, filename: str) -> Optional[Dict]:
        """
        在所有启用的数据源中匹配图片
        
        Args:
            filename: 图片文件名
            
        Returns:
            匹配到的记录字典，未找到返回None
        """
        for source_name in self.get_enabled_sources():
            result = self.match_image_in_source(source_name, filename)
            if result:
                return result
        return None
    
    def batch_match_images(
        self, 
        filenames: List[str]
    ) -> Dict[str, Optional[Dict]]:
        """
        批量匹配图片
        
        Args:
            filenames: 图片文件名列表
            
        Returns:
            {文件名: 匹配结果} 字典
        """
        results = {}
        for filename in filenames:
            results[filename] = self.match_image_all_sources(filename)
        return results
    
    def get_quarter(self, date_obj) -> str:
        """
        根据日期获取季度
        
        Args:
            date_obj: datetime对象
            
        Returns:
            季度字符串，如 "2025_Q4"
        """
        if not date_obj:
            from datetime import datetime
            date_obj = datetime.now()
        
        year = date_obj.year
        month = date_obj.month
        quarter = (month - 1) // 3 + 1
        return f"{year}_Q{quarter}"
    
    def build_target_path(self, alarm_name: str, alarm_time) -> str:
        """
        构建目标分类路径
        
        Args:
            alarm_name: 告警名称
            alarm_time: 告警时间
            
        Returns:
            相对路径，如 "烟雾检测/2025_Q4"
        """
        target_config = self.get_target_directory()
        structure = target_config.get('structure', '{alarm_name}/{year}_Q{quarter}')
        
        quarter_str = self.get_quarter(alarm_time)
        year = quarter_str.split('_')[0]
        quarter = quarter_str.split('_Q')[1]
        
        # 清理告警名称中的非法字符
        safe_alarm_name = self._sanitize_dirname(alarm_name or '未分类')
        
        return structure.format(
            alarm_name=safe_alarm_name,
            year=year,
            quarter=quarter
        )
    
    def _sanitize_dirname(self, name: str) -> str:
        """清理目录名中的非法字符"""
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()


if __name__ == '__main__':
    # 测试代码
    manager = DataSourceManager()
    
    print("=== 数据源配置 ===")
    for name, source in manager.get_enabled_sources().items():
        print(f"- {name}: {source['description']}")
    
    print("\n=== 目标目录 ===")
    target = manager.get_target_directory()
    print(f"基础路径: {target.get('base_path')}")
    print(f"目录结构: {target.get('structure')}")
