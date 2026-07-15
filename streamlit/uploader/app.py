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
from sf_common import get_active_session, get_sf_config

st.set_page_config(page_title="Snowflake アップローダ", page_icon="📤", layout="wide")

# ===== 接続環境（共通）=====
session = get_active_session()
cfg = get_sf_config()
ctx = LoadContext(
    session=session, cfg=cfg, db="USERDB_D_P01_LAK", schema="USER_SMCB_01"
)

# ===== メイン =====
st.title("📤 Snowflake アップローダ")
label = st.selectbox("アップロード対象", list(DATASETS.keys()))
render_dataset(ctx, DATASETS[label])
