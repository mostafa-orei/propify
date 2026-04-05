-- 01-create-tables.sql

-- Drop everything first to start clean
DROP MATERIALIZED VIEW IF EXISTS borough_counts;
DROP TABLE IF EXISTS rightmove_properties CASCADE;
DROP TABLE IF EXISTS london_boroughs CASCADE;

-- Main properties table
CREATE TABLE rightmove_properties (
    id INT PRIMARY KEY,
    borough TEXT,
    bedrooms DOUBLE PRECISION,
    bathrooms DOUBLE PRECISION,
    summary TEXT,
    displayAddress TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    updateDate TEXT,
    price_amount BIGINT,
    displaySize_sqft DOUBLE PRECISION,
    property_sub_type TEXT,
    geom GEOMETRY(Point, 4326)
);

CREATE INDEX idx_properties_geom ON rightmove_properties USING GIST(geom);
CREATE INDEX idx_properties_borough ON rightmove_properties(borough);
CREATE INDEX idx_properties_price ON rightmove_properties(price_amount);

-- Borough boundaries table
CREATE TABLE london_boroughs (
    name TEXT PRIMARY KEY,
    geom GEOMETRY(MultiPolygon, 4326)
);

CREATE INDEX idx_boroughs_geom ON london_boroughs USING GIST(geom);

-- Materialized view for borough counts (useful for low zoom)
CREATE MATERIALIZED VIEW borough_counts AS
SELECT 
    b.name AS borough,
    COUNT(p.id) AS home_count,
    ST_Centroid(b.geom) AS center_geom
FROM london_boroughs b
LEFT JOIN rightmove_properties p ON ST_Contains(b.geom, p.geom)
GROUP BY b.name, b.geom;