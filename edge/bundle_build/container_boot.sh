start_delay=${START_DELAY:-5}
sleep $start_delay

redis_id=$(docker run -d -v $REDIS_CONF:/usr/local/etc/redis/redis.conf redis:alpine redis-server /usr/local/etc/redis/redis.conf)
redis_host=$(docker inspect --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" $redis_id)
redis_port=${REDIS_PORT:-6379}

openresty_id=$(docker run -d -v $OPENRESTY_CONF:/usr/local/openresty/nginx/conf/nginx.conf -e "REDIS_HOST=$redis_host" -e "REDIS_PORT=$redis_port" openresty/openresty:alpine)
openresty_host=$(docker inspect --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" $openresty_id)
openresty_port=${OPENRESTY_PORT:-80}
echo $openresty_host:$openresty_port
# export PATH="/usr/local/openresty/nginx/sbin:$PATH"
# export REDIS_HOST="$redis_host"
# export REDIS_PORT="$redis_port"
# nginx

python -m expire_daemon --redis-host $redis_host --redis-port $redis_port &
python -m ready_daemon --redis-host $redis_host --redis-port $redis_port &
python -m dx_agent --redis-host $redis_host --redis-port $redis_port &
python -m transporter &
socat TCP-LISTEN:80,fork TCP:$openresty_host:$openresty_port &

tail -f /dev/null
