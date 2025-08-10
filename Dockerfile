FROM python:3.13.5-slim

WORKDIR /app

COPY pyproject.toml ./

# 時間設定、安裝 uv、同步虛擬環境
RUN ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime \
    && echo "Asia/Taipei" > /etc/timezone \
    && pip install uv --no-cache-dir \
    && uv sync

COPY . .