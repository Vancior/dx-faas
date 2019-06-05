FROM python:3-stretch

RUN apt-get update
RUN apt-get install -y apt-transport-https
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch main contrib non-free" > /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-backports main contrib non-free" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security stretch/updates main contrib non-free" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y curl


# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g cnpm --registry=https://registry.npm.taobao.org
RUN cnpm install -g jsonata
RUN cnpm install -g redis

ENV NODE_PATH /usr/lib/node_modules

# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# COPY setup.py ./
# COPY dx_runtime ./dx_runtime
# RUN python setup.py install

# CMD ["python", "-m", "dx_runtime"]
WORKDIR /data
COPY . ./
ENTRYPOINT node /data/index.js
