-- =====================================================
-- 数据资产管理系统 - PostgreSQL 建表脚本 (优化版 v2)
-- 数据库名称: asset_catalog
-- 创建日期: 2026-01-05
-- 优化要点: 使用JSONB提高扩展性和维护性
-- =====================================================

-- 连接到数据库
\c asset_catalog;

-- =====================================================
-- 1. 核心表：asset_catalog（资产目录表）
-- =====================================================

CREATE TABLE IF NOT EXISTS asset_catalog (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    
    -- 物理属性
    filepath VARCHAR(1024) NOT NULL UNIQUE,
    filename VARCHAR(512) NOT NULL,
    filesize BIGINT NOT NULL,
    file_ext VARCHAR(20),
    mtime TIMESTAMP NOT NULL,
    
    -- 身份指纹
    md5_hash VARCHAR(32) NOT NULL,
    
    -- 业务标签
    industry VARCHAR(64),
    category VARCHAR(128),
    subcategory VARCHAR(128),
    year INTEGER,
    quarter VARCHAR(10),
    
    -- 资产状态
    status VARCHAR(20) DEFAULT 'ready',
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,
    
    -- 扩展元数据
    metadata JSONB,
    
    CONSTRAINT chk_status CHECK (status IN ('ready', 'deprecated', 'error', 'processing'))
);

-- 创建索引
CREATE INDEX idx_filepath ON asset_catalog(filepath);
CREATE INDEX idx_md5_hash ON asset_catalog(md5_hash);
CREATE INDEX idx_mtime ON asset_catalog(mtime DESC);
CREATE INDEX idx_status ON asset_catalog(status);
CREATE INDEX idx_industry_category ON asset_catalog(industry, category);
CREATE INDEX idx_registered_at ON asset_catalog(registered_at DESC);
CREATE INDEX idx_metadata_gin ON asset_catalog USING GIN(metadata);

-- 添加注释
COMMENT ON TABLE asset_catalog IS '资产目录核心表（不变）';
COMMENT ON COLUMN asset_catalog.filepath IS 'NAS文件完整路径，唯一标识';
COMMENT ON COLUMN asset_catalog.metadata IS 'JSONB扩展元数据';

-- =====================================================
-- 2. 业务表：emergency_alarm_assets（优化版）
-- =====================================================

CREATE TABLE IF NOT EXISTS emergency_alarm_assets (
    -- 核心主键和关联
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT NOT NULL REFERENCES asset_catalog(id) ON DELETE CASCADE,
    
    -- 核心业务字段（高频查询+必须索引）
    alarm_id INTEGER,                        -- 原始告警ID
    alarm_type INTEGER,                      -- 告警类型：400/401/402
    alarm_name VARCHAR(32),                  -- 告警名称（如：火点检测报警事件）
    dev_code VARCHAR(64),                    -- 设备编码
    alarm_time TIMESTAMP,                    -- 告警时间
    analysis TEXT,                           -- AI分析结果
    area_code VARCHAR(64),                   -- 区域编码
    status SMALLINT DEFAULT 1,               -- 告警状态：1待复核 2已处理
    
    -- 扩展业务数据（JSONB存储）
    business_data JSONB,                     -- 其他业务字段
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_ea_asset_id ON emergency_alarm_assets(asset_id);
CREATE INDEX idx_ea_alarm_id ON emergency_alarm_assets(alarm_id);
CREATE INDEX idx_ea_alarm_time ON emergency_alarm_assets(alarm_time DESC);
CREATE INDEX idx_ea_alarm_type ON emergency_alarm_assets(alarm_type);
CREATE INDEX idx_ea_alarm_name ON emergency_alarm_assets(alarm_name);
CREATE INDEX idx_ea_dev_code ON emergency_alarm_assets(dev_code);
CREATE INDEX idx_ea_area_code_time ON emergency_alarm_assets(area_code, alarm_time DESC);
CREATE INDEX idx_ea_status ON emergency_alarm_assets(status);
CREATE INDEX idx_ea_business_data ON emergency_alarm_assets USING GIN(business_data);

-- 添加注释
COMMENT ON TABLE emergency_alarm_assets IS '应急告警图片资产表（实际生产版本）';
COMMENT ON COLUMN emergency_alarm_assets.alarm_name IS '告警名称：火点检测报警事件/烟雾检测报警事件/烟火检测报警事件等';
COMMENT ON COLUMN emergency_alarm_assets.dev_code IS '设备编码';
COMMENT ON COLUMN emergency_alarm_assets.alarm_time IS '告警时间';
COMMENT ON COLUMN emergency_alarm_assets.analysis IS 'AI分析结果';
COMMENT ON COLUMN emergency_alarm_assets.business_data IS 'JSONB存储：dev_name, channel_code, channel_name, area_name, process_user_id, process_user_name, process_time, source, level, analysis_time等扩展字段';

-- =====================================================
-- 3. 业务表：emergency_channel_images（优化版）
-- =====================================================

CREATE TABLE IF NOT EXISTS emergency_channel_images (
    -- 核心主键和关联
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT NOT NULL REFERENCES asset_catalog(id) ON DELETE CASCADE,
    
    -- 核心业务字段
    channel_code VARCHAR(255) NOT NULL,      -- 通道编码
    image_type VARCHAR(32),                  -- 图片类型：snapshot/map/other
    area_code VARCHAR(255),                  -- 区域编码
    
    -- 位置信息（地图查询必需）
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    
    -- 扩展通道信息（JSONB存储）
    channel_info JSONB,                      -- 所有其他通道字段
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_eci_asset_id ON emergency_channel_images(asset_id);
CREATE INDEX idx_eci_channel_code ON emergency_channel_images(channel_code);
CREATE INDEX idx_eci_image_type ON emergency_channel_images(image_type);
CREATE INDEX idx_eci_area_code ON emergency_channel_images(area_code);
CREATE INDEX idx_eci_location ON emergency_channel_images(latitude, longitude);
CREATE INDEX idx_eci_channel_info ON emergency_channel_images USING GIN(channel_info);

-- 添加注释
COMMENT ON TABLE emergency_channel_images IS '应急视频通道图片资产表（优化版）';
COMMENT ON COLUMN emergency_channel_images.channel_info IS 'JSONB存储：channel_name, channel_type, image_desc, position, dev_code, online_state, img_status, img_details_status, tag_name, tag_code等';

-- =====================================================
-- 4. 辅助表：data_issues（数据问题反馈表）
-- =====================================================

CREATE TABLE IF NOT EXISTS data_issues (
    id BIGSERIAL PRIMARY KEY,
    
    -- 关联asset_catalog（可选）
    asset_id BIGINT REFERENCES asset_catalog(id) ON DELETE SET NULL,
    filepath VARCHAR(1024),
    
    -- 问题描述
    issue_type VARCHAR(32),                  -- corrupt/missing/format_error
    error_msg TEXT,
    
    -- 报告信息
    reported_by VARCHAR(64),
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 处理状态
    status VARCHAR(20) DEFAULT 'pending',    -- pending/resolved/ignored
    resolved_by VARCHAR(64),
    resolved_at TIMESTAMP,
    resolution_note TEXT,
    
    CONSTRAINT chk_issue_status CHECK (status IN ('pending', 'resolved', 'ignored'))
);

-- 创建索引
CREATE INDEX idx_issue_status ON data_issues(status);
CREATE INDEX idx_issue_reported_at ON data_issues(reported_at DESC);
CREATE INDEX idx_issue_asset_id ON data_issues(asset_id);

COMMENT ON TABLE data_issues IS '数据问题反馈表';

-- =====================================================
-- 5. 新增表：file_operation_log（文件操作日志表）
-- =====================================================

CREATE TABLE IF NOT EXISTS file_operation_log (
    id BIGSERIAL PRIMARY KEY,
    
    -- 操作信息
    operation_type VARCHAR(20) NOT NULL,     -- upload/delete/move/rename/copy
    filepath_old VARCHAR(1024),
    filepath_new VARCHAR(1024),
    filesize BIGINT,
    
    -- 操作人信息
    operated_by VARCHAR(64),
    operation_ip VARCHAR(45),
    operated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 结果
    status VARCHAR(20) DEFAULT 'success',    -- success/failed
    error_msg TEXT,
    
    -- 扩展信息
    extra_info JSONB,
    
    CONSTRAINT chk_operation_type CHECK (operation_type IN ('upload', 'delete', 'move', 'rename', 'copy')),
    CONSTRAINT chk_operation_status CHECK (status IN ('success', 'failed'))
);

-- 创建索引
CREATE INDEX idx_fol_operation_type ON file_operation_log(operation_type);
CREATE INDEX idx_fol_operated_at ON file_operation_log(operated_at DESC);
CREATE INDEX idx_fol_operated_by ON file_operation_log(operated_by);
CREATE INDEX idx_fol_filepath_old ON file_operation_log(filepath_old);
CREATE INDEX idx_fol_status ON file_operation_log(status);

COMMENT ON TABLE file_operation_log IS '文件操作日志表：记录所有文件操作审计信息';

-- =====================================================
-- 6. 新增表：asset_scan_tasks（资产扫描任务表）
-- =====================================================

CREATE TABLE IF NOT EXISTS asset_scan_tasks (
    id BIGSERIAL PRIMARY KEY,
    
    -- 任务时间
    task_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_end_time TIMESTAMP,
    
    -- 扫描范围
    scan_directory VARCHAR(512),
    
    -- 统计信息
    files_scanned INTEGER DEFAULT 0,
    files_added INTEGER DEFAULT 0,
    files_updated INTEGER DEFAULT 0,
    files_deprecated INTEGER DEFAULT 0,
    
    -- 任务状态
    task_status VARCHAR(20) DEFAULT 'running',  -- running/completed/failed/cancelled
    error_msg TEXT,
    
    -- 扩展信息
    scan_result JSONB,
    
    CONSTRAINT chk_task_status CHECK (task_status IN ('running', 'completed', 'failed', 'cancelled'))
);

-- 创建索引
CREATE INDEX idx_ast_task_start_time ON asset_scan_tasks(task_start_time DESC);
CREATE INDEX idx_ast_task_status ON asset_scan_tasks(task_status);
CREATE INDEX idx_ast_scan_directory ON asset_scan_tasks(scan_directory);

COMMENT ON TABLE asset_scan_tasks IS '资产扫描任务表：监控注册脚本运行状态';

-- =====================================================
-- 7. 创建视图：友好的查询接口
-- =====================================================

-- 视图1：完整的告警资产视图（封装JSONB）
CREATE OR REPLACE VIEW v_alarm_assets_full AS
SELECT 
    ea.id,
    ea.asset_id,
    ea.alarm_id,
    ea.alarm_type,
    ea.alarm_time,
    ea.area_code,
    ea.status,
    -- 从JSONB提取常用字段
    ea.business_data->>'dev_code' AS dev_code,
    ea.business_data->>'dev_name' AS dev_name,
    ea.business_data->>'alarm_name' AS alarm_name,
    ea.business_data->>'channel_code' AS channel_code,
    ea.business_data->>'channel_name' AS channel_name,
    ea.business_data->>'area_name' AS area_name,
    (ea.business_data->>'process_user_id')::INTEGER AS process_user_id,
    ea.business_data->>'process_user_name' AS process_user_name,
    (ea.business_data->>'process_time')::TIMESTAMP AS process_time,
    (ea.business_data->>'source')::INTEGER AS source,
    (ea.business_data->>'level')::SMALLINT AS level,
    ea.business_data->>'analysis' AS analysis,
    (ea.business_data->>'analysis_time')::TIMESTAMP AS analysis_time,
    ea.business_data AS all_business_data,
    -- 关联资产信息
    ac.filepath,
    ac.filename,
    ac.filesize,
    ac.md5_hash,
    ac.status AS asset_status,
    ea.created_at,
    ea.updated_at
FROM emergency_alarm_assets ea
JOIN asset_catalog ac ON ea.asset_id = ac.id
WHERE ac.status = 'ready';

COMMENT ON VIEW v_alarm_assets_full IS '告警资产完整视图：封装JSONB字段提供传统表查询体验';

-- 视图2：通道图片资产视图（封装JSONB）
CREATE OR REPLACE VIEW v_channel_images_full AS
SELECT 
    eci.id,
    eci.asset_id,
    eci.channel_code,
    eci.image_type,
    eci.area_code,
    eci.latitude,
    eci.longitude,
    -- 从JSONB提取常用字段
    eci.channel_info->>'channel_name' AS channel_name,
    (eci.channel_info->>'channel_type')::INTEGER AS channel_type,
    eci.channel_info->>'image_desc' AS image_desc,
    eci.channel_info->>'position' AS position,
    eci.channel_info->>'dev_code' AS dev_code,
    (eci.channel_info->>'online_state')::INTEGER AS online_state,
    (eci.channel_info->>'img_status')::SMALLINT AS img_status,
    eci.channel_info->>'tag_name' AS tag_name,
    eci.channel_info AS all_channel_info,
    -- 关联资产信息
    ac.filepath,
    ac.filename,
    ac.filesize,
    ac.md5_hash,
    eci.created_at,
    eci.updated_at
FROM emergency_channel_images eci
JOIN asset_catalog ac ON eci.asset_id = ac.id
WHERE ac.status = 'ready';

COMMENT ON VIEW v_channel_images_full IS '通道图片资产视图：封装JSONB字段提供传统表查询体验';

-- 视图3：扫描任务统计视图
CREATE OR REPLACE VIEW v_scan_tasks_summary AS
SELECT 
    DATE(task_start_time) AS scan_date,
    COUNT(*) AS total_tasks,
    SUM(files_scanned) AS total_scanned,
    SUM(files_added) AS total_added,
    SUM(files_updated) AS total_updated,
    SUM(files_deprecated) AS total_deprecated,
    COUNT(*) FILTER (WHERE task_status = 'completed') AS completed_tasks,
    COUNT(*) FILTER (WHERE task_status = 'failed') AS failed_tasks
FROM asset_scan_tasks
GROUP BY DATE(task_start_time)
ORDER BY scan_date DESC;

COMMENT ON VIEW v_scan_tasks_summary IS '扫描任务统计视图：按日汇总扫描情况';

-- =====================================================
-- 8. 示例数据
-- =====================================================

-- 插入示例资产
INSERT INTO asset_catalog (filepath, filename, filesize, file_ext, mtime, md5_hash, industry, category, subcategory, year, quarter, metadata)
VALUES 
    ('/data/nas_data/10_Official_Library/02_应急_安全/02_历史告警归档/森林防火/2024_Q1/alarm_001.jpg', 
     'alarm_001.jpg', 
     1024000, 
     '.jpg', 
     '2024-01-15 14:30:00', 
     'abc123def456789', 
     '应急_安全', 
     '历史告警归档', 
     '森林防火', 
     2024, 
     '2024_Q1',
     '{"original_source": "应急平台", "upload_user": "admin"}'::jsonb);

-- 插入示例告警资产（使用JSONB）
INSERT INTO emergency_alarm_assets (asset_id, alarm_id, alarm_type, alarm_time, area_code, status, business_data)
VALUES 
    (1, 
     12345, 
     400, 
     '2024-01-15 14:30:00', 
     'AREA001', 
     1,
     jsonb_build_object(
         'dev_code', 'DEV001',
         'dev_name', '森林监控设备A',
         'alarm_name', '森林防火',
         'channel_code', 'CH001',
         'channel_name', '通道1号',
         'area_name', '某某林区',
         'source', 2,
         'level', 2,
         'analysis', 'AI检测到疑似火情',
         'link_screen', 1,
         'link_live', 1
     ));

-- 插入示例扫描任务
INSERT INTO asset_scan_tasks (scan_directory, files_scanned, files_added, task_status)
VALUES 
    ('/data/nas_data/10_Official_Library', 100, 5, 'completed');

-- =====================================================
-- 9. 维护函数
-- =====================================================

-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 应用触发器
CREATE TRIGGER update_emergency_alarm_assets_updated_at
    BEFORE UPDATE ON emergency_alarm_assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_emergency_channel_images_updated_at
    BEFORE UPDATE ON emergency_channel_images
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 10. 权限配置
-- =====================================================

-- 创建只读角色
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'asset_reader') THEN
        CREATE ROLE asset_reader LOGIN PASSWORD 'ReadOnlyPass@2024';
    END IF;
END
$$;

-- 授予只读权限
GRANT CONNECT ON DATABASE asset_catalog TO asset_reader;
GRANT USAGE ON SCHEMA public TO asset_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO asset_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO asset_reader;

-- admin完整权限
GRANT ALL PRIVILEGES ON DATABASE asset_catalog TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;

-- =====================================================
-- 11. 查询示例
-- =====================================================

\echo ''
\echo '=========================================='
\echo '查询示例'
\echo '=========================================='

-- 示例1：通过视图查询告警（像传统表一样）
\echo '示例1：查询2024年所有告警：'
SELECT id, alarm_id, alarm_name, alarm_time, dev_name 
FROM v_alarm_assets_full 
WHERE alarm_time >= '2024-01-01' 
LIMIT 5;

-- 示例2：JSONB字段查询
\echo '示例2：查询特定设备的告警：'
SELECT id, alarm_id, alarm_time, business_data->>'dev_code' AS dev_code
FROM emergency_alarm_assets 
WHERE business_data->>'dev_code' = 'DEV001';

-- 示例3：检查JSONB是否包含某字段
\echo '示例3：查找包含自定义字段的记录：'
SELECT id, alarm_id FROM emergency_alarm_assets WHERE business_data ? 'custom_field';

-- =====================================================
-- 完成信息
-- =====================================================

\echo ''
\echo '=========================================='
\echo '数据库初始化完成！（优化版 v2）'
\echo '=========================================='
\echo '已创建的表：'
\echo '  1. asset_catalog - 资产目录核心表'
\echo '  2. emergency_alarm_assets - 告警图片资产（优化版，使用JSONB）'
\echo '  3. emergency_channel_images - 通道图片资产（优化版，使用JSONB）'
\echo '  4. data_issues - 数据问题反馈表'
\echo '  5. file_operation_log - 文件操作日志表 [NEW]'
\echo '  6. asset_scan_tasks - 资产扫描任务表 [NEW]'
\echo ''
\echo '已创建的视图：'
\echo '  1. v_alarm_assets_full - 告警资产完整视图（封装JSONB）'
\echo '  2. v_channel_images_full - 通道图片完整视图（封装JSONB）'
\echo '  3. v_scan_tasks_summary - 扫描任务统计视图 [NEW]'
\echo ''
\echo '优化要点：'
\echo '  ✓ 使用JSONB存储可变字段，提高扩展性'
\echo '  ✓ 核心字段保留为独立列，保证查询性能'
\echo '  ✓ 通过视图封装，提供传统表查询体验'
\echo '  ✓ 新增运维表，支持审计和监控'
\echo '=========================================='

-- 显示表列表
\dt
