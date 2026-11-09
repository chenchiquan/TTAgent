FROM python:3.11-slim
WORKDIR /app

# chromadb 等包需要 gcc 编译，先装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖（利用层缓存，改代码不重装）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷代码
COPY . .

EXPOSE 8000
# 容器内 uvicorn 要监听 0.0.0.0 才能被其他容器访问
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
