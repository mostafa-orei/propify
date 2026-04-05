# daily-data-challenge

### create tiles
docker run -e JAVA_TOOL_OPTIONS="-Xmx1g" -v "$(pwd)/data":/data ghcr.io/onthegomap/planetiler:latest --download --area=london

docker exec -it realestate-postgis psql -U postgres -d realestate -f /docker-entrypoint-initdb.d/01-create-tables.sql

docker exec -it realestate-postgis psql -U postgres -d realestate -f /docker-entrypoint-initdb.d/02-import-csv.sql

docker exec -it realestate-postgis psql -U postgres -d realestate -f /docker-entrypoint-initdb.d/03-import-boroughs.sql

docker compose down
docker compose up -d

python3 -m http.server 8080


add filters beside index.html
house complex apartment ....
budget and size range label with slide range
bedroom 1 2 3 4 5+
bathroom 1 2 3 4 5+
apply

make filters work on apply and select part of homes and show in map

search button bottem of map that have a ai animation in it that in touch expand on touch with textfield for ai prompt and disappear on touch on map and have a send button beside text field

label of price with white background and bold gray price with pond icon beside

change view of filters icon when a filter activate
change ai icon to simple ai animation and background of ai fab and move it to side panel with animation that shows chats with ai
change slide item for price and size to one slide tool for max and min and change label of price with changing in tool
side panel move from right to left
change view of layer in map
add tilt when a property selected or higher zoom level then 16 relatively increase tilt with zoom
add icon for properties type buttons


add random image for homes
scrape center of london data with images