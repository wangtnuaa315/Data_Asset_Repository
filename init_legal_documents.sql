-- =====================================================
-- 法律文书模块数据库表
-- =====================================================

-- 1. 法律文书主表
CREATE TABLE IF NOT EXISTS legal_documents (
    id BIGSERIAL PRIMARY KEY,
    doc_id VARCHAR(64) UNIQUE NOT NULL,          -- 原始UUID（来自Excel）
    title TEXT NOT NULL,                          -- 案件标题
    
    -- 分类字段（高频查询，建索引）
    case_type VARCHAR(32),                        -- 案件类型：民事/刑事/行政/赔偿
    case_cause VARCHAR(255),                      -- 案由
    trial_procedure VARCHAR(64),                  -- 审理程序：一审/二审/再审
    region VARCHAR(128),                          -- 地域
    judgment_year INTEGER,                        -- 裁判年份
    judgment_result VARCHAR(128),                 -- 裁判结果
    
    -- 金额（可空）
    claim_amount DECIMAL(18,2),                   -- 诉请金额
    judgment_amount DECIMAL(18,2),                -- 判决金额
    fine_amount DECIMAL(18,2),                    -- 罚金
    
    -- 长文本内容（不建索引）
    cited_laws TEXT,                              -- 引用法条
    judgment_section TEXT,                        -- 裁判结果段
    argument_section TEXT,                        -- 诉辩意见段
    fact_section TEXT,                            -- 事实认定段
    reasoning_section TEXT,                       -- 裁判理由段
    
    -- 元数据
    source_file VARCHAR(512),                     -- 来源文件名
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 核心索引
CREATE INDEX IF NOT EXISTS idx_ld_case_type ON legal_documents(case_type);
CREATE INDEX IF NOT EXISTS idx_ld_case_cause ON legal_documents(case_cause);
CREATE INDEX IF NOT EXISTS idx_ld_trial_procedure ON legal_documents(trial_procedure);
CREATE INDEX IF NOT EXISTS idx_ld_region ON legal_documents(region);
CREATE INDEX IF NOT EXISTS idx_ld_judgment_year ON legal_documents(judgment_year);
CREATE INDEX IF NOT EXISTS idx_ld_judgment_result ON legal_documents(judgment_result);

-- 复合索引（常用组合查询）
CREATE INDEX IF NOT EXISTS idx_ld_type_cause ON legal_documents(case_type, case_cause);
CREATE INDEX IF NOT EXISTS idx_ld_region_year ON legal_documents(region, judgment_year DESC);

-- 标题模糊搜索索引
CREATE INDEX IF NOT EXISTS idx_ld_title_trgm ON legal_documents USING gin(title gin_trgm_ops);

-- 2. 案由树形结构表（来自 JSON 文件）
CREATE TABLE IF NOT EXISTS legal_cause_tree (
    id SERIAL PRIMARY KEY,
    cause_name VARCHAR(255) NOT NULL,             -- 案由名称
    case_type VARCHAR(32) NOT NULL,               -- 顶层类别：民事/刑事/赔偿/行政
    parent_id INTEGER REFERENCES legal_cause_tree(id),  -- 父节点
    level INTEGER NOT NULL DEFAULT 1,             -- 层级 1-5
    full_path TEXT,                               -- 完整路径，用 > 分隔
    sort_order INTEGER DEFAULT 0,                 -- 排序顺序
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lct_case_type ON legal_cause_tree(case_type);
CREATE INDEX IF NOT EXISTS idx_lct_parent ON legal_cause_tree(parent_id);
CREATE INDEX IF NOT EXISTS idx_lct_level ON legal_cause_tree(level);

-- 3. 案由统计视图（从实际数据中统计）
CREATE OR REPLACE VIEW v_legal_cause_stats AS
SELECT 
    case_type,
    case_cause,
    COUNT(*) as doc_count,
    MIN(judgment_year) as min_year,
    MAX(judgment_year) as max_year
FROM legal_documents
WHERE case_cause IS NOT NULL
GROUP BY case_type, case_cause
ORDER BY case_type, doc_count DESC;

-- 4. 地域统计视图
CREATE OR REPLACE VIEW v_legal_region_stats AS
SELECT 
    region,
    COUNT(*) as doc_count
FROM legal_documents
WHERE region IS NOT NULL
GROUP BY region
ORDER BY doc_count DESC;

-- 5. 裁判结果统计视图
CREATE OR REPLACE VIEW v_legal_result_stats AS
SELECT 
    judgment_result,
    COUNT(*) as doc_count
FROM legal_documents
WHERE judgment_result IS NOT NULL
GROUP BY judgment_result
ORDER BY doc_count DESC;

-- 添加表注释
COMMENT ON TABLE legal_documents IS '法律文书主表 - 存储裁判文书数据';
COMMENT ON TABLE legal_cause_tree IS '案由树形结构表 - 存储案由层级关系';

COMMENT ON COLUMN legal_documents.doc_id IS '原始文档ID（UUID）';
COMMENT ON COLUMN legal_documents.title IS '案件标题';
COMMENT ON COLUMN legal_documents.case_type IS '案件类型：民事/刑事/行政/赔偿';
COMMENT ON COLUMN legal_documents.case_cause IS '案由';
COMMENT ON COLUMN legal_documents.trial_procedure IS '审理程序：一审/二审/再审/申诉';
COMMENT ON COLUMN legal_documents.region IS '地域';
COMMENT ON COLUMN legal_documents.judgment_year IS '裁判年份';
COMMENT ON COLUMN legal_documents.judgment_result IS '裁判结果';
COMMENT ON COLUMN legal_documents.cited_laws IS '引用法条';
COMMENT ON COLUMN legal_documents.judgment_section IS '裁判结果段';
COMMENT ON COLUMN legal_documents.reasoning_section IS '裁判理由段';

-- 启用 pg_trgm 扩展（用于模糊搜索）
CREATE EXTENSION IF NOT EXISTS pg_trgm;
