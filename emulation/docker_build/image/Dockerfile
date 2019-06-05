FROM python:3-stretch

RUN apt-get update
RUN apt-get install -y apt-transport-https
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch main contrib non-free" > /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-backports main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security stretch/updates main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update

RUN apt-get install -y iproute2 iputils-ping net-tools

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

ENV EMULATION_MODE dev
# ENV CLOUD_HOST 127.0.0.1
ENV START_TIME 10
ENV RUN_INTERVAL 1

WORKDIR /data
COPY ./dx_emulation ./dx_emulation
RUN ls
RUN pip install -r dx_emulation/requirements.txt
RUN python dx_emulation/setup.py install
