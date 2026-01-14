#!/usr/bin/env python3
"""
资产注册脚本
register_assets.py

功能：
1. 增量扫描 10_Official_Library/ 目录
2. 计算文件MD5哈希值
3. 解析路径标签（industry, category等）
4. 写入 asset_catalog 表
5. 记录扫描任务到 asset_scan_tasks 表
"""

import os
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import psycopg2
from psycopg2.extras import Json
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/data_asset/logs/register_assets.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AssetRegistrar:
    """资产注册器"""
    
    def __init__(self, config_path='/opt/data_asset/config.yaml'):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.nas_base = self.config['nas']['base_path']
        self.scan_directory = os.path.join(self.nas_base, '10_Official_Library')
        
        # PostgreSQL连接
        self.pg_config = self.config['postgresql']
        
        # 扫描任务ID
        self.task_id = None
        
        # 统计信息
        self.stats = {
            'scanned': 0,
            'added': 0,
            'updated': 0,
            'deprecated': 0,
            'errors': 0
        }
        
        # 上次扫描时间
        self.last_scan_time = None
    
    def connect_db(self):
        """连接PostgreSQL"""
        return psycopg2.connect(
            host=self.pg_config['host'],
            port=self.pg_config['port'],
            user=self.pg_config['user'],
            password=self.pg_config['password'],
            database=self.pg_config['database']
        )
    
    def calculate_md5(self, filepath: str) -> str:
        """计算文件MD5哈希值"""
        try:
            md5_hash = hashlib.md5()
            with open(filepath, 'rb') as f:
                # 分块读取避免大文件内存问题
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            logger.error(f"计算MD5失败: {filepath}, 错误: {e}")
            return None
    
    def parse_path_tags(self, filepath: str) -> Dict:
        """
        从文件路径解析业务标签
        
        路径格式示例：
        /data/nas_data/10_Official_Library/02_应急_安全/02_历史告警归档/森林防火/2024_Q1/alarm_001.jpg
        
        Returns:
            {
                'industry': '应急_安全',
                'category': '历史告警归档',
                'subcategory': '森林防火',
                'year': 2024,
                'quarter': '2024_Q1'
            }
        """
        try:
            # 获取相对于Official_Library的路径
            rel_path = os.path.relpath(filepath, self.scan_directory)
            parts = rel_path.split(os.sep)
            
            tags = {
                'industry': None,
                'category': None,
                'subcategory': None,
                'year': None,
                'quarter': None
            }
            
            # 解析industry (如 "02_应急_安全")
            if len(parts) > 0 and '_' in parts[0]:
                tags['industry'] = '_'.join(parts[0].split('_')[1:])
            
            # 解析category (如 "02_历史告警归档")
            if len(parts) > 1 and '_' in parts[1]:
                tags['category'] = '_'.join(parts[1].split('_')[1:])
            
            # 解析subcategory (如 "森林防火")
            if len(parts) > 2:
                tags['subcategory'] = parts[2]
            
            # 解析quarter和year (如 "2024_Q1")
            if len(parts) > 3 and '_Q' in parts[3]:
                quarter_str = parts[3]
                tags['quarter'] = quarter_str
                year_str = quarter_str.split('_')[0]
                try:
                    tags['year'] = int(year_str)
                except:
                    pass
            
            return tags
            
        except Exception as e:
            logger.error(f"解析路径标签失败: {filepath}, 错误: {e}")
            return {}
    
    def get_last_scan_time(self) -> Optional[datetime]:
        """获取上次扫描时间"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT MAX(mtime) FROM asset_catalog
                WHERE status = 'ready'
            """)
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            return result[0] if result[0] else None
            
        except Exception as e:
            logger.error(f"获取上次扫描时间失败: {e}")
            return None
    
    def start_scan_task(self) -> int:
        """开始扫描任务"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO asset_scan_tasks (
                    scan_directory, task_status
                ) VALUES (%s, %s)
                RETURNING id
            """, (self.scan_directory, 'running'))
            
            task_id = cur.fetchone()[0]
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"📝 扫描任务已创建，ID: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"创建扫描任务失败: {e}")
            return None
    
    def finish_scan_task(self, status='completed', error_msg=None):
        """完成扫描任务"""
        if not self.task_id:
            return
        
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE asset_scan_tasks SET
                    task_end_time = NOW(),
                    files_scanned = %s,
                    files_added = %s,
                    files_updated = %s,
                    files_deprecated = %s,
                    task_status = %s,
                    error_msg = %s,
                    scan_result = %s
                WHERE id = %s
            """, (
                self.stats['scanned'],
                self.stats['added'],
                self.stats['updated'],
                self.stats['deprecated'],
                status,
                error_msg,
                Json({'errors': self.stats['errors']}),
                self.task_id
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ 扫描任务已完成，ID: {self.task_id}")
            
        except Exception as e:
            logger.error(f"完成扫描任务失败: {e}")
    
    def register_asset(self, filepath: str):
        """注册单个资产"""
        try:
            # 获取文件信息
            stat = os.stat(filepath)
            filename = os.path.basename(filepath)
            file_ext = Path(filepath).suffix.lower()
            filesize = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # 计算MD5
            md5_hash = self.calculate_md5(filepath)
            if not md5_hash:
                self.stats['errors'] += 1
                return
            
            # 解析标签
            tags = self.parse_path_tags(filepath)
            
            # 写入数据库（使用UPSERT）
            conn = self.connect_db()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO asset_catalog (
                    filepath, filename, filesize, file_ext, mtime, md5_hash,
                    industry, category, subcategory, year, quarter, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (filepath) DO UPDATE SET
                    filesize = EXCLUDED.filesize,
                    mtime = EXCLUDED.mtime,
                    md5_hash = EXCLUDED.md5_hash,
                    last_verified_at = NOW(),
                    updated_at = NOW()
                RETURNING (xmax = 0) AS is_insert
            """, (
                filepath,
                filename,
                filesize,
                file_ext,
                mtime,
                md5_hash,
                tags.get('industry'),
                tags.get('category'),
                tags.get('subcategory'),
                tags.get('year'),
                tags.get('quarter'),
                'ready'
            ))
            
            is_insert = cur.fetchone()[0]
            
            conn.commit()
            cur.close()
            conn.close()
            
            if is_insert:
                self.stats['added'] += 1
                logger.debug(f"➕ 新增资产: {filename}")
            else:
                self.stats['updated'] += 1
                logger.debug(f"🔄 更新资产: {filename}")
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ 注册资产失败: {filepath}, 错误: {e}")
    
    def scan_files(self):
        """扫描文件"""
        logger.info(f"🔍 开始扫描目录: {self.scan_directory}")
        
        # 支持的文件类型
        allowed_exts = self.config.get('allowed_extensions', [
            '.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xls', '.xlsx'
        ])
        
        for root, dirs, files in os.walk(self.scan_directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                file_ext = Path(filepath).suffix.lower()
                
                # 过滤文件类型
                if file_ext not in allowed_exts:
                    continue
                
                self.stats['scanned'] += 1
                
                # 增量扫描：只处理新文件或修改的文件
                if self.last_scan_time:
                    try:
                        mtime = datetime.fromtimestamp(os.stat(filepath).st_mtime)
                        if mtime <= self.last_scan_time:
                            continue
                    except:
                        pass
                
                # 注册资产
                self.register_asset(filepath)
                
                # 每1000个文件输出一次进度
                if self.stats['scanned'] % 1000 == 0:
                    logger.info(f"进度: 已扫描 {self.stats['scanned']} 个文件")
    
    def mark_deprecated_assets(self):
        """标记已删除的文件"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            # 查询所有ready状态的资产
            cur.execute("""
                SELECT id, filepath FROM asset_catalog
                WHERE status = 'ready'
            """)
            
            assets = cur.fetchall()
            
            for asset_id, filepath in assets:
                if not os.path.exists(filepath):
                    # 文件已被删除，标记为deprecated
                    cur.execute("""
                        UPDATE asset_catalog SET
                            status = 'deprecated',
                            last_verified_at = NOW()
                        WHERE id = %s
                    """, (asset_id,))
                    
                    self.stats['deprecated'] += 1
                    logger.info(f"🗑️ 标记已删除: {filepath}")
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"标记已删除资产失败: {e}")
    
    def print_summary(self):
        """打印扫描摘要"""
        logger.info("=" * 60)
        logger.info("资产注册摘要")
        logger.info("=" * 60)
        logger.info(f"扫描文件数: {self.stats['scanned']}")
        logger.info(f"新增资产: {self.stats['added']}")
        logger.info(f"更新资产: {self.stats['updated']}")
        logger.info(f"标记删除: {self.stats['deprecated']}")
        logger.info(f"错误数: {self.stats['errors']}")
        logger.info("=" * 60)
    
    def run(self):
        """执行资产注册"""
        logger.info("🚀 开始资产注册...")
        
        try:
            # 开始扫描任务
            self.task_id = self.start_scan_task()
            
            # 获取上次扫描时间（增量扫描）
            self.last_scan_time = self.get_last_scan_time()
            if self.last_scan_time:
                logger.info(f"📅 上次扫描时间: {self.last_scan_time}")
            
            # 扫描文件
            self.scan_files()
            
            # 标记已删除的文件
            self.mark_deprecated_assets()
            
            # 打印摘要
            self.print_summary()
            
            # 检查是否有错误
            if self.stats['errors'] > 0:
                # 如果所有操作都失败了，标记为失败
                if self.stats['added'] == 0 and self.stats['updated'] == 0:
                    self.finish_scan_task('failed', f"全部{self.stats['errors']}个文件注册失败")
                    logger.error(f"❌ 资产注册失败：{self.stats['errors']}个错误")
                    raise Exception(f"资产注册失败：{self.stats['errors']}个错误")
                else:
                    # 部分成功
                    self.finish_scan_task('completed')
                    logger.warning(f"⚠️ 资产注册完成，但有{self.stats['errors']}个错误")
            else:
                # 完成扫描任务
                self.finish_scan_task('completed')
                logger.info("✅ 资产注册完成！")
            
        except Exception as e:
            logger.error(f"❌ 资产注册失败: {e}")
            self.finish_scan_task('failed', str(e))
            raise


def main():
    """主函数"""
    registrar = AssetRegistrar()
    registrar.run()


if __name__ == '__main__':
    main()
