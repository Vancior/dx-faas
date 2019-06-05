#!/usr/bin/env bash
# 安装docker相关

# 拉取openresty redis的镜像，并且将dx_runtime的镜像build/pull

# 根据配置启动redis容器

# # redis.conf
# notify-keyspace-events "Ex"

docker run -d -p 6379:6379 -v $PWD/redis.conf:/usr/local/etc/redis/redis.conf redis:alpine redis-server /usr/local/etc/redis/redis.conf

# 根据配置指定lua脚本位置启动openresty镜像


# # nginx.conf
# server {
#     listen 80;
#
#     location / {
#         set $upstream '';
#         access_by_lua_block {
#             local redis = require "resty.redis"
#             local client = redis:new()
#             local ok, err = client:connect("172.17.42.1", 6379)
#             if not ok then
#                 ngx.say("failed to connect: ", err)
#                 return
#             end
#
#             matches, err = ngx.re.match(ngx.var.uri, "/([0-9a-f]+)(/.*)?")
#             if not matches then
#                 ngx.say("failed to regex: ", err)
#                 return
#             end
#
#             local function_status = client:get(matches[1]..':status')
#             if not function_status then
#                 ngx.say("function not found")
#                 return
#             end
#
#             if function_status == 'running' then
#                 ngx.var.upstream = client:get(matches[1]..':ip')
#             else
#                 ngx.say('function not ready', function_status)
#                 return
#             end
#             client:incr(matches[1]..':visit_count')
#             -- ngx.log(ngx.DEBUG, matches[1])
#             -- ngx.log(ngx.DEBUG, matches[2])
#             -- io.write(ngx.var.uri)
#             -- ngx.say('hello')
#             client:set_keepalive(10000, 100)  # 毫秒，池大小
#         }
#         proxy_pass http://$upstream;
#     }
# }

docker run -d -p 80:80 -v $PWD/nginx.conf:/etc/nginx/conf.d/default.conf openresty/openresty:alpine

# 运行函数过期回收守护进程

# 运行dx_agent

