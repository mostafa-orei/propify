# Propify

#### scrap data from righmove is in scrap folder

### create tiles with planetiler
docker run -e JAVA_TOOL_OPTIONS="-Xmx1g" -v "$(pwd)/data":/data ghcr.io/onthegomap/planetiler:latest --download --area=london

### create tables and import data in db
docker exec -it realestate-postgis psql -U postgres -d realestate -f /docker-entrypoint-initdb.d/01-create-tables.sql

docker exec -it realestate-postgis psql -U postgres -d realestate -f /docker-entrypoint-initdb.d/02-import-csv.sql

docker exec -it realestate-postgis psql -U postgres -d realestate -f /docker-entrypoint-initdb.d/03-import-boroughs.sql

### start docker compose
docker compose up -d

### run app
python3 -m http.server 8080
