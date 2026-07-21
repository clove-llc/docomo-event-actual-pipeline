#!/usr/bin/env bash
# ローカルの Streamlit アプリを Snowflake (Streamlit in Snowflake) へデプロイ／更新する。
#
# 前提:
#   - .streamlit/secrets.toml に接続情報（database/schema/warehouse 含む）が設定済み
#   - snowflake-connector-python がインストール済み（pip install -r requirements.txt）
#
# 使い方:
#   ./deploy.sh                 # 既定アプリ名 UPLOADER_XLSX で更新
#   ./deploy.sh MY_APP_NAME     # アプリ名を指定
set -euo pipefail

cd "$(dirname "$0")"

APP_NAME="${1:-UPLOADER_XLSX}"
PY="${PYTHON:-python}"

echo "=== Streamlit in Snowflake へデプロイ: ${APP_NAME} ==="
"${PY}" deploy.py "${APP_NAME}"
