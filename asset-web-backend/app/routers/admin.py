"""
admin.py

管理员API路由 - 文件管理和脚本执行
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from pydantic import BaseModel
from typing import List, Optional
from app.services.admin_service import admin_service
from app.services.auth_service import require_admin


router = APIRouter(prefix='/admin', tags=['管理员'])


class FileInfo(BaseModel):
    """文件信息"""
    name: str
    path: str
    is_dir: bool
    size: int
    modified: str


class FileListResponse(BaseModel):
    """文件列表响应"""
    files: List[FileInfo]
    total: int


class UploadResponse(BaseModel):
    """上传响应"""
    filename: str
    size: int
    message: str


class DeleteRequest(BaseModel):
    """删除请求"""
    path: str


class CreateDirRequest(BaseModel):
    """创建目录请求"""
    name: str


class ScriptRequest(BaseModel):
    """脚本执行请求"""
    script: str  # parse, verify, register, import


class ScriptResponse(BaseModel):
    """脚本执行响应"""
    success: bool
    output: str
    error: str


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool


@router.get('/files', response_model=FileListResponse)
async def list_files(
    subdir: str = '',
    current_user: dict = Depends(require_admin)
):
    """
    列出new_uploads目录中的文件
    
    - **subdir**: 子目录路径（可选）
    """
    files = admin_service.list_files(subdir)
    return FileListResponse(files=files, total=len(files))


@router.post('/upload', response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin)
):
    """
    上传文件到new_uploads目录
    """
    content = await file.read()
    result = await admin_service.save_file(file.filename, content)
    
    return UploadResponse(
        filename=result['filename'],
        size=result['size'],
        message='上传成功'
    )


@router.delete('/files')
async def delete_file(
    request: DeleteRequest,
    current_user: dict = Depends(require_admin)
):
    """
    删除文件或目录
    
    - **path**: 相对于new_uploads的路径
    """
    success = admin_service.delete_file(request.path)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='文件不存在'
        )
    
    return MessageResponse(message='删除成功', success=True)


@router.post('/directories')
async def create_directory(
    request: CreateDirRequest,
    current_user: dict = Depends(require_admin)
):
    """
    创建目录
    
    - **name**: 目录名称
    """
    success = admin_service.create_directory(request.name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='目录已存在或创建失败'
        )
    
    return MessageResponse(message='创建成功', success=True)


@router.post('/scripts/run', response_model=ScriptResponse)
async def run_script(
    request: ScriptRequest,
    current_user: dict = Depends(require_admin)
):
    """
    执行脚本
    
    - **script**: 脚本名称
        - parse: 解析元数据
        - verify: 文件分类验证
        - register: 资产注册
        - import: 业务数据导入
    """
    result = await admin_service.run_script(request.script)
    
    return ScriptResponse(
        success=result['success'],
        output=result.get('output', ''),
        error=result.get('error', '')
    )


@router.get('/scripts/list')
async def list_scripts(current_user: dict = Depends(require_admin)):
    """
    获取可执行的脚本列表
    """
    return {
        'scripts': [
            {
                'id': 'parse',
                'name': '1. 解析元数据',
                'description': '解析上传的CSV/Excel文件，匹配图片生成metadata_emergency.csv',
                'file': 'parse_metadata.py'
            },
            {
                'id': 'verify',
                'name': '2. 文件分类',
                'description': '根据告警类型和时间分类归档图片',
                'file': 'verify_structure.py'
            },
            {
                'id': 'register',
                'name': '3. 资产注册',
                'description': '将归档的文件注册到资产目录',
                'file': 'register_assets.py'
            },
            {
                'id': 'import',
                'name': '4. 业务数据导入',
                'description': '导入告警业务数据到PostgreSQL',
                'file': 'import_from_csv.py'
            }
        ]
    }
