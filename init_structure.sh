#!/bin/bash

# ==========================================
# 数据资产管理系统 - 物理层初始化脚本
# 用于�?NAS 未到位时，在本地模拟标准目录结构
# ==========================================

# 1. 设置模拟 NAS 的根目录 (根据实际磁盘空间修改)
# 建议放在空间最大的挂载点下，例�?/data/nas_data �?/home/nas_data
MOCK_NAS_ROOT="/data/nas_data"

echo "正在初始化模�?NAS 环境..."
echo "根目�? $MOCK_NAS_ROOT"

# 2. 创建核心层级 (The Bookshelf)
# - p 确保父目录存�?mkdir -p "$MOCK_NAS_ROOT/00_Work_Area/new_uploads"
mkdir -p "$MOCK_NAS_ROOT/00_Work_Area/trash_bin"
mkdir -p "$MOCK_NAS_ROOT/10_Official_Library"

# 3. 创建业务分类目录 (根据方案文档)
# 10_Official_Library 下的一级分�?LIB_ROOT="$MOCK_NAS_ROOT/10_Official_Library"

# --- 01_法院_司法 ---
mkdir -p "$LIB_ROOT/01_法院_司法/01_法律法规�?
mkdir -p "$LIB_ROOT/01_法院_司法/02_裁判文书�?
mkdir -p "$LIB_ROOT/01_法院_司法/03_电子卷宗�?
mkdir -p "$LIB_ROOT/01_法院_司法/04_业务参考库"

# --- 02_应急_安全 ---
mkdir -p "$LIB_ROOT/02_应急_安全/01_预案体系�?
mkdir -p "$LIB_ROOT/02_应急_安全/02_历史告警归档"
mkdir -p "$LIB_ROOT/02_应急_安全/03_应急资源库"
mkdir -p "$LIB_ROOT/02_应急_安全/04_案例复盘"

# --- 03_通用 ---
mkdir -p "$LIB_ROOT/03_通用"

# 4. 创建示例年份文件�?(方便测试)
# 在裁判文书库下创建当前年�?YEAR=$(date +%Y)
mkdir -p "$LIB_ROOT/01_法院_司法/02_裁判文书�?$YEAR/民事"
mkdir -p "$LIB_ROOT/01_法院_司法/02_裁判文书�?$YEAR/刑事"

# 5. 设置权限
# 确保当前用户可读�?chmod -R 755 "$MOCK_NAS_ROOT"

echo "=========================================="
echo "�?初始化完成！"
echo "📂 您的工作区已就绪: $MOCK_NAS_ROOT/00_Work_Area"
echo "📚 您的交付区已就绪: $LIB_ROOT"
echo "=========================================="
echo "下一步建议："
echo "1. 将测试文件上传到 00_Work_Area/new_uploads"
echo "2. 尝试按照规范手动移动�?10_Official_Library"
