-- =====================================================
-- 法院卷宗模块 - PostgreSQL 建表脚本
-- 数据库名称: asset_catalog
-- 创建日期: 2026-01-15
-- =====================================================

-- 连接到数据库
\c asset_catalog;

-- =====================================================
-- 1. 案件主表：court_cases
-- =====================================================

CREATE TABLE IF NOT EXISTS court_cases (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    
    -- 案件标识
    case_code VARCHAR(128) UNIQUE NOT NULL,    -- 案件唯一编号
    ah VARCHAR(64),                             -- 案号（如(2024)浙01民初123）
    aj_mc VARCHAR(1024),                        -- 案件名称
    
    -- 法院信息
    ent_code VARCHAR(128),                      -- 法院分级码
    fymc VARCHAR(128),                          -- 法院名称
    
    -- 案件分类
    ajlx_id VARCHAR(32),                        -- 案件类型编号
    ajlx_mc VARCHAR(1024),                      -- 案件类型描述
    ay_id VARCHAR(32),                          -- 案由编号
    ay_ms VARCHAR(1024),                        -- 案由描述
    
    -- 审判阶段与关联
    trial_stage SMALLINT,                       -- 审判阶段: 1=一审, 2=二审
    first_instance_ah VARCHAR(255),             -- 一审案号（二审时关联）
    ys_ah VARCHAR(255),                         -- 原审案号
    ys_fymc VARCHAR(255),                       -- 原审法院名称
    ys_ajbh VARCHAR(255),                       -- 原审案件编号
    
    -- 承办信息
    cbr_code VARCHAR(128),                      -- 承办人编号
    cbr_mc VARCHAR(32),                         -- 承办人名称
    fgzl_code VARCHAR(128),                     -- 法官助理编号
    fgzl_mc VARCHAR(32),                        -- 法官助理名称
    cbbm_code VARCHAR(128),                     -- 承办部门编号
    cbbm_mc VARCHAR(32),                        -- 承办部门名称
    
    -- 时间节点
    larq VARCHAR(22),                           -- 立案日期
    ktrq DATE,                                  -- 开庭日期
    
    -- 金额信息
    bdje FLOAT,                                 -- 标的金额
    
    -- 状态字段
    close_status SMALLINT DEFAULT 0,            -- 结案状态: 0=未结案, 1=已结案
    judgement_status SMALLINT,                  -- 判决书状态: 1=待生成, 2=已生成
    sync_dossier_status SMALLINT,               -- 卷宗同步状态
    
    -- 扩展字段
    extra_data JSONB,                           -- 其他扩展字段
    
    -- 元数据
    isdel SMALLINT DEFAULT 0,                   -- 是否删除: 0=未删除, 1=已删除
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_cc_case_code ON court_cases(case_code);
CREATE INDEX idx_cc_ah ON court_cases(ah);
CREATE INDEX idx_cc_ent_code ON court_cases(ent_code);
CREATE INDEX idx_cc_cbr_code ON court_cases(cbr_code);
CREATE INDEX idx_cc_trial_stage ON court_cases(trial_stage);
CREATE INDEX idx_cc_larq ON court_cases(larq);
CREATE INDEX idx_cc_ktrq ON court_cases(ktrq);
CREATE INDEX idx_cc_ay_id ON court_cases(ay_id);
CREATE INDEX idx_cc_ajlx_id ON court_cases(ajlx_id);

COMMENT ON TABLE court_cases IS '法院案件主表';
COMMENT ON COLUMN court_cases.case_code IS '案件唯一编号';
COMMENT ON COLUMN court_cases.ah IS '案号，如(2024)浙01民初123';
COMMENT ON COLUMN court_cases.trial_stage IS '审判阶段: 1=一审, 2=二审';
COMMENT ON COLUMN court_cases.first_instance_ah IS '一审案号（二审案件时填写）';

-- =====================================================
-- 2. 卷宗表：court_dossiers
-- =====================================================

CREATE TABLE IF NOT EXISTS court_dossiers (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    
    -- 卷宗标识
    dossier_code VARCHAR(128) UNIQUE,           -- 卷宗唯一标识号
    case_code VARCHAR(128) NOT NULL,            -- 案件唯一编号（关联court_cases）
    
    -- 文件关联
    asset_id BIGINT REFERENCES asset_catalog(id) ON DELETE SET NULL,
    file_code VARCHAR(128),                     -- 文件唯一标识号
    
    -- 文件信息
    original_name TEXT NOT NULL,                -- 原始文件名
    original_suffix VARCHAR(64),                -- 文件类型（小写）
    
    -- 层级结构
    parent_dossier_code VARCHAR(128),           -- 父节点
    sfml SMALLINT DEFAULT 0,                    -- 是否目录: 0=否, 1=是
    priority INTEGER,                           -- 排序优先级
    
    -- 卷宗分类
    dossier_type INTEGER DEFAULT 0,             -- 卷宗类型: 0=卷宗, 1=当庭证据
    dossier_category SMALLINT,                  -- 卷宗分类: 1-13
    classify VARCHAR(255),                      -- 卷宗分类文本
    summary TEXT,                               -- 文件摘要
    
    -- AI处理状态
    cpm_status SMALLINT,                        -- OCR识别状态: 1=待识别, 2=成功
    simplify_status SMALLINT,                   -- 文本精简状态: 1=待精简, 2=完成
    rag_status SMALLINT,                        -- RAG入库状态: 1=待入库, 2=入库中, 3=成功
    
    -- 元数据
    upload_time VARCHAR(255),                   -- 上传时间
    isdel SMALLINT DEFAULT 0,                   -- 是否删除
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    CONSTRAINT fk_court_dossiers_case FOREIGN KEY (case_code) 
        REFERENCES court_cases(case_code) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_cd_dossier_code ON court_dossiers(dossier_code);
CREATE INDEX idx_cd_case_code ON court_dossiers(case_code);
CREATE INDEX idx_cd_asset_id ON court_dossiers(asset_id);
CREATE INDEX idx_cd_file_code ON court_dossiers(file_code);
CREATE INDEX idx_cd_sfml ON court_dossiers(sfml);
CREATE INDEX idx_cd_dossier_category ON court_dossiers(dossier_category);
CREATE INDEX idx_cd_parent ON court_dossiers(parent_dossier_code);
CREATE INDEX idx_cd_cpm_status ON court_dossiers(cpm_status);

COMMENT ON TABLE court_dossiers IS '法院案件卷宗表';
COMMENT ON COLUMN court_dossiers.dossier_category IS '卷宗分类: 1=起诉状 2=答辩状 3=证据 4=其他 5=原审判决书 6=庭审笔录 7=诉讼请求变更 8=反诉状 9=量刑建议书 10=行政复议决定书 11=立案审批表 12=调解笔录 13=调解协议';
COMMENT ON COLUMN court_dossiers.sfml IS '是否目录: 0=文件, 1=目录';

-- =====================================================
-- 3. 创建视图：案件卷宗统计视图
-- =====================================================

CREATE OR REPLACE VIEW v_court_case_dossier_stats AS
SELECT 
    cc.id,
    cc.case_code,
    cc.ah,
    cc.aj_mc,
    cc.fymc,
    cc.ajlx_mc,
    cc.ay_ms,
    cc.trial_stage,
    cc.first_instance_ah,
    cc.cbr_mc,
    cc.larq,
    cc.ktrq,
    cc.bdje,
    cc.close_status,
    cc.isdel,  -- 添加 isdel 字段用于查询过滤
    -- 卷宗统计
    COUNT(cd.id) AS dossier_count,
    COUNT(cd.id) FILTER (WHERE cd.dossier_category = 1) > 0 AS has_indictment,     -- 起诉状
    COUNT(cd.id) FILTER (WHERE cd.dossier_category = 2) > 0 AS has_defense,        -- 答辩状
    COUNT(cd.id) FILTER (WHERE cd.dossier_category = 5) > 0 AS has_judgement,      -- 判决书
    COUNT(cd.id) FILTER (WHERE cd.dossier_category = 6) > 0 AS has_court_record,   -- 庭审笔录
    COUNT(cd.id) FILTER (WHERE cd.dossier_category = 8) > 0 AS has_counterclaim,   -- 反诉状
    cc.created_at,
    cc.updated_at
FROM court_cases cc
LEFT JOIN court_dossiers cd ON cc.case_code = cd.case_code AND cd.isdel = 0
WHERE cc.isdel = 0
GROUP BY cc.id;

COMMENT ON VIEW v_court_case_dossier_stats IS '案件卷宗统计视图：包含各类卷宗是否存在的标志';

-- =====================================================
-- 4. 自动更新 updated_at 触发器
-- =====================================================

CREATE TRIGGER update_court_cases_updated_at
    BEFORE UPDATE ON court_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_court_dossiers_updated_at
    BEFORE UPDATE ON court_dossiers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 完成信息
-- =====================================================

\echo ''
\echo '==========================================';
\echo '法院卷宗模块数据库初始化完成';
\echo '==========================================';
\echo '已创建的表：';
\echo '  1. court_cases - 案件主表';
\echo '  2. court_dossiers - 卷宗表';
\echo '';
\echo '已创建的视图：';
\echo '  1. v_court_case_dossier_stats - 案件卷宗统计视图';
\echo '==========================================';
