"""
admin_service.py

管理员服务 - 处理文件管理和脚本执行
"""

import os
import shutil
import subprocess
import asyncio
from typing import List, Dict, Optional
from datetime import datetime


class AdminService:
    """管理员服务"""
    
    def __init__(self, base_path: str = '/data/nas_data'):
        self.base_path = base_path
        self.work_area = os.path.join(base_path, '00_Work_Area')
        self.new_uploads = os.path.join(self.work_area, 'new_uploads')
        
        # 脚本路径
        self.scripts_dir = '/opt/data_asset/scripts/emergency'
        self.common_scripts_dir = '/opt/data_asset/scripts/common'
        
        # 脚本执行状态
        self.running_tasks = {}
    
    def ensure_upload_dir(self):
        """确保上传目录存在"""
        os.makedirs(self.new_uploads, exist_ok=True)
    
    def list_files(self, subdir: str = '') -> List[Dict]:
        """
        列出目录中的文件
        
        Args:
            subdir: 子目录路径
            
        Returns:
            文件列表
        """
        target_dir = os.path.join(self.new_uploads, subdir) if subdir else self.new_uploads
        
        if not os.path.exists(target_dir):
            return []
        
        files = []
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            stat = os.stat(item_path)
            files.append({
                'name': item,
                'path': os.path.join(subdir, item) if subdir else item,
                'is_dir': os.path.isdir(item_path),
                'size': stat.st_size if not os.path.isdir(item_path) else 0,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # 目录在前，文件在后
        files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        return files
    
    async def save_file(self, filename: str, content: bytes) -> Dict:
        """
        保存上传的文件
        
        Args:
            filename: 文件名
            content: 文件内容
            
        Returns:
            保存结果
        """
        self.ensure_upload_dir()
        
        file_path = os.path.join(self.new_uploads, filename)
        
        # 处理文件名冲突
        if os.path.exists(file_path):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(file_path):
                filename = f"{base}_{counter}{ext}"
                file_path = os.path.join(self.new_uploads, filename)
                counter += 1
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {
            'filename': filename,
            'path': file_path,
            'size': len(content)
        }
    
    def delete_file(self, filepath: str) -> bool:
        """
        删除文件
        
        Args:
            filepath: 相对于new_uploads的路径
            
        Returns:
            是否成功
        """
        full_path = os.path.join(self.new_uploads, filepath)
        
        if not os.path.exists(full_path):
            return False
        
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        
        return True
    
    def create_directory(self, dirname: str) -> bool:
        """
        创建目录
        
        Args:
            dirname: 目录名
            
        Returns:
            是否成功
        """
        dir_path = os.path.join(self.new_uploads, dirname)
        
        if os.path.exists(dir_path):
            return False
        
        os.makedirs(dir_path)
        return True
    
    async def run_script(self, script_name: str) -> Dict:
        """
        执行脚本
        
        Args:
            script_name: 脚本名称
            
        Returns:
            执行结果
        """
        # 脚本映射
        scripts = {
            'parse': os.path.join(self.scripts_dir, 'parse_metadata.py'),
            'verify': os.path.join(self.scripts_dir, 'verify_structure.py'),
            'register': os.path.join(self.common_scripts_dir, 'register_assets.py'),
            'import': os.path.join(self.scripts_dir, 'import_from_csv.py'),
        }
        
        script_path = scripts.get(script_name)
        if not script_path:
            return {
                'success': False,
                'error': f'未知脚本: {script_name}',
                'output': ''
            }
        
        if not os.path.exists(script_path):
            return {
                'success': False,
                'error': f'脚本不存在: {script_path}',
                'output': ''
            }
        
        try:
            # 执行脚本
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd='/opt/data_asset'
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else '',
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '脚本执行超时（5分钟）',
                'output': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': ''
            }


# 创建单例
admin_service = AdminService()
