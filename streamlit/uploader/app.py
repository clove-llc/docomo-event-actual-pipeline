"""Snowflake アップローダ（エントリポイント）

上部のセレクタで対象（実績データ / 各種マスタ）を選び、選んだ Excel を Snowflake へロードする。
取込仕様は datasets.py の DatasetSpec が一元管理し、UI は loaders/ui.py の汎用 render が描画する。

起動（ローカル）:
    cd streamlit/uploader
    pip install -r requirements.txt
    streamlit run app.py

デプロイ（SiSへ更新）:
    ./deploy.sh
"""

from __future__ import annotations

import streamlit as st

from datasets import DATASETS
from loaders.spec import LoadContext
from loaders.ui import render_dataset
from sf_common import current_db_schema, get_active_session, get_sf_config

st.set_page_config(page_title="Snowflake アップローダ", page_icon="📤", layout="wide")

# ===== 接続環境（共通）=====
session = get_active_session()
cfg = get_sf_config()
db, schema = current_db_schema(session, cfg)
with st.sidebar:
    st.header("ロード先")
    if session is not None:
        st.success("Snowflake 内で実行中（アクティブセッション）")
    elif cfg:
        st.success("secrets.toml の [snowflake] を検出")
        st.caption(f"account: `{cfg.get('account', '(未設定)')}` / user: `{cfg.get('user', '(未設定)')}`")
    else:
        st.warning("認証情報が未設定です（.streamlit/secrets.toml）。")
    db = st.text_input("Database", value=db)
    schema = st.text_input("Schema", value=schema)

ctx = LoadContext(session=session, cfg=cfg, db=db, schema=schema)

# ===== メイン =====
st.title("📤 Snowflake アップローダ")
label = st.selectbox("アップロード対象", list(DATASETS.keys()))
render_dataset(ctx, DATASETS[label])
