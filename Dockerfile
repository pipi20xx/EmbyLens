# Stage 1: Build Frontend
FROM node:20-slim as frontend-builder
WORKDIR /frontend

# 设置 NPM 国内镜像源
RUN npm config set registry https://registry.npmmirror.com

COPY frontend/package.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Build Backend and Final Image
FROM python:3.10-slim
WORKDIR /app

# 设置 APT 国内镜像源 (针对 Debian)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 设置 PIP 国内镜像源
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端代码
COPY backend/ /app/

# 复制前端编译结果到后端静态目录
COPY --from=frontend-builder /frontend/dist /app/static

EXPOSE 6565

# 确保数据目录存在
RUN mkdir -p /app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6565"]