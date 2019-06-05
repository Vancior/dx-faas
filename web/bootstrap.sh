docker run -d -p 32768:3306 -e MYSQL_ROOT_PASSWORD=924597121 mysql:latest
docker run -p 80:80 -v $PWD/nginx.conf:/etc/nginx/conf.d/default.conf -v $PWD/frontend/dist:/data/www nginx:latest
docker run \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=9001:8080 \
  --detach=true \
  --name=cadvisor \
  google/cadvisor:latest

docker run -d -p 80:80 -v $PWD/nginx.conf:/etc/nginx/conf.d/default.conf -v $PWD/frontend/dist:/data/www --name gateway nginx:latest