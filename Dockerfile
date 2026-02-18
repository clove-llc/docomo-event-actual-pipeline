FROM python:3.13-slim

# 必要最低限のツール
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Poetryインストール
RUN pip install --no-cache-dir poetry

# 仮想環境を作らない（超重要）
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# 依存定義を先にコピー（キャッシュ最適化）
COPY pyproject.toml poetry.lock* ./

# 依存インストール（本番用のみ）
RUN poetry install --no-interaction --no-ansi --only main

# ソースコードコピー
COPY . .

# Job実行コマンド
CMD ["python", "main.py"]
