FROM python:3-slim-stretch

# set up tuna sources
RUN apt-get update
RUN apt-get install -y apt-transport-https
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch main contrib non-free" > /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-backports main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security stretch/updates main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update

# install docker-ce
RUN apt-get install -y ca-certificates curl gnupg2 software-properties-common
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
RUN apt-get update
RUN apt-get install -y --fix-missing docker-ce docker-ce-cli containerd.io

WORKDIR /dx_edge
COPY ./dx_agent2 ./dx_agent2
COPY ./expire_daemon ./expire_daemon
COPY ./ready_daemon ./ready_daemon
COPY ./transporter ./transporter
COPY ./redis.conf ./redis.conf
# COPY ./nginx_main.conf ./nginx.conf

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /dx_edge/dx_agent2
RUN pip install -r requirements.txt
RUN python setup.py install

# COPY ../dx_runtime2 .
# RUN pip install -r dx_runtime2/requirements.txt
# RUN python dx_runtime2/setup.py install

WORKDIR /dx_edge/expire_daemon
RUN pip install -r requirements.txt
RUN python setup.py install

WORKDIR /dx_edge/ready_daemon
RUN pip install -r requirements.txt
RUN python setup.py install

WORKDIR /dx_edge/transporter
RUN pip install -r requirements.txt
RUN python setup.py install

RUN apt-get update
RUN apt-get install -y socat wget unzip iproute2 iputils-ping net-tools

RUN wget -qO - https://openresty.org/package/pubkey.gpg | apt-key add -
RUN apt-get -y install software-properties-common
RUN add-apt-repository -y "deb http://openresty.org/package/debian $(lsb_release -sc) openresty"
RUN apt-get update
RUN apt-get install -y openresty
COPY ./nginx_main.conf /usr/local/openresty/nginx/conf/nginx.conf

WORKDIR /
ENV START_DELAY 5
ENV REDIS_CONF /home/hujuntao/gitrepo/dx-proto/edge/redis.conf
ENV OPENRESTY_CONF /home/hujuntao/gitrepo/dx-proto/edge/nginx_main.conf
ENV FUNCTION_WAREHOUSE /home/hujuntao/deploy/functions
COPY bundle_build/container_boot.sh ./boot.sh
# ENTRYPOINT bash boot.sh
