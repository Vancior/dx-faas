FROM python:3-stretch

RUN apt-get update
RUN apt-get install -y apt-transport-https
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch main contrib non-free" > /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-backports main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security stretch/updates main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y curl iproute2 iputils-ping net-tools

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /data
COPY . ./
RUN pip install -r requirements.txt