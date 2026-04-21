FROM python:3.13.5-slim

WORKDIR /app

# 時間設定
RUN ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime \
    && echo "Asia/Taipei" > /etc/timezone

ENV PYTHONPYCACHEPREFIX=/tmp/pycache

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# install deps
COPY pyproject.toml uv.lock ./

ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# install playwright
RUN uv run playwright install --with-deps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["uv", "run", "main.py"]