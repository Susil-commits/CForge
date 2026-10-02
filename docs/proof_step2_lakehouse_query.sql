-- Step 2 Proof Query: Which certified tables contain PII and are consumed by dashboards?
-- Executed directly against ContextForge Parquet Metadata Lakehouse

WITH RECURSIVE dashboard_lineage AS (
    -- Direct edges pointing to dashboards
    SELECT
        source_asset_id,
        target_asset_id,
        CAST(target_asset_id AS VARCHAR) AS downstream_path
    FROM read_parquet('data/lakehouse/lineage_edges.parquet')
    WHERE target_asset_id LIKE '%.dashboard.%' 
       OR target_asset_id LIKE 'dashboard.%'

    UNION ALL

    -- Follow edges backwards to discover source tables
    SELECT
        e.source_asset_id,
        e.target_asset_id,
        CAST(e.target_asset_id || ' -> ' || dl.downstream_path AS VARCHAR) AS downstream_path
    FROM read_parquet('data/lakehouse/lineage_edges.parquet') e
    JOIN dashboard_lineage dl ON e.target_asset_id = dl.source_asset_id
),
pii_columns AS (
    -- Identify all columns with PII classifications
    SELECT DISTINCT
        a.asset_id AS column_asset_id,
        a.parent_id AS table_asset_id,
        a.name AS column_name,
        t.tag_name,
        t.tag_value AS pii_type,
        t.confidence
    FROM read_parquet('data/lakehouse/assets.parquet') a
    JOIN read_parquet('data/lakehouse/tags.parquet') t ON a.asset_id = t.asset_id
    WHERE t.tag_name = 'PII'
),
certified_tables AS (
    -- Filter strictly for CERTIFIED production tables
    SELECT
        asset_id AS table_asset_id,
        name AS table_name,
        owner,
        certification_status,
        quality_score
    FROM read_parquet('data/lakehouse/assets.parquet')
    WHERE asset_type = 'TABLE'
      AND certification_status = 'CERTIFIED'
)
SELECT DISTINCT
    ct.table_name,
    ct.certification_status,
    ct.owner,
    pc.column_name,
    pc.pii_type,
    dl.downstream_path AS consumed_by_dashboard
FROM certified_tables ct
JOIN pii_columns pc ON ct.table_asset_id = pc.table_asset_id
JOIN dashboard_lineage dl ON (ct.table_asset_id = dl.source_asset_id OR pc.column_asset_id = dl.source_asset_id)
ORDER BY ct.table_name, pc.column_name;
