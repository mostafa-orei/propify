-- Import CSV (run once)
COPY rightmove_properties (
    id, borough, bedrooms, bathrooms, summary, displayAddress,
    latitude, longitude, updateDate, price_amount,
    displaySize_sqft, property_sub_type
)
FROM '/data/rightmove_properties_all_boroughs.csv'
DELIMITER ',' CSV HEADER;

-- Create geometry from lat/lon
UPDATE rightmove_properties
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Optional: add borough count view (for low-zoom labels)
CREATE MATERIALIZED VIEW IF NOT EXISTS borough_counts AS
SELECT 
    b.name AS borough,
    COUNT(p.id) AS home_count,
    ST_Centroid(b.geom) AS center_geom
FROM london_boroughs b
LEFT JOIN rightmove_properties p ON ST_Contains(b.geom, p.geom)
GROUP BY b.name, b.geom;