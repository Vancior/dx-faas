FROM python:alpine

WORKDIR /usr/src/app

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY setup.py ./
COPY dx_runtime ./dx_runtime
RUN python setup.py install

CMD ["python", "-m", "dx_runtime"]
