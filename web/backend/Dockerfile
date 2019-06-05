FROM python:3-slim-stretch


RUN apt-get update
RUN apt-get install -y apt-transport-https
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch main contrib non-free" > /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-backports main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security stretch/updates main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y curl iproute2 iputils-ping net-tools
RUN apt-get install -y wget
RUN apt-get install -y unzip procps

WORKDIR /download
RUN wget https://dl.minio.io/client/mc/release/linux-amd64/mc
RUN chmod +x ./mc
RUN /download/mc config host add minio http://172.17.42.1:9000 Vancior 924597121

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /data
COPY . ./
RUN pip install -r requirements.txt

# ENTRYPOINT python deploy-service/main.py
