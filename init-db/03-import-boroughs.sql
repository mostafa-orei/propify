-- 03-import-boroughs.sql

WITH features AS (
    SELECT jsonb_array_elements(
        (pg_read_file('/data/london_boundaries.geojson')::jsonb)->'features'
    ) AS feature
),
parsed AS (
    SELECT 
        feature->'properties'->>'name' AS name,
        ST_SetSRID(
            ST_GeomFromGeoJSON(feature->>'geometry'), 
            4326
        ) AS geom
    FROM features
)
INSERT INTO london_boroughs (name, geom)
SELECT name, geom
FROM parsed
WHERE name IS NOT NULL
ON CONFLICT (name) DO UPDATE 
SET geom = EXCLUDED.geom;

REFRESH MATERIALIZED VIEW borough_counts;

SELECT '✅ Boroughs imported:' AS msg, COUNT(*) FROM london_boroughs;