"""Streamlit UI（spec 駆動の汎用 render とロード実行）。"""

from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from sf_common import connect_snowflake, exec_sql, load_dataframe

from loaders.extract import flat_extract, wide_extract
from loaders.spec import DatasetSpec, LoadContext
from loaders.transform import build_ddl, cast_by_type


def yyyymm(sheet: str) -> str:
    """シート名の先頭から年(4桁)＋月 → YYYYMM（例: '2025.11（更新済）' → '202511'）。"""
    m = re.match(r"\s*(\d{4})\D*(\d{1,2})", sheet)
    if m:
        return m.group(1) + m.group(2).zfill(2)
    return re.sub(r"\D", "", sheet)[:6]


def run_upload(ctx: LoadContext, table: str, fqtn: str, ddl: str, df: pd.DataFrame) -> None:
    """CREATE OR REPLACE TABLE → ロード（進捗を表示）。"""
    can_run = (ctx.session is not None or bool(ctx.cfg)) and bool(ctx.db) and bool(ctx.schema)
    if not can_run:
        st.info("※ 認証情報・Database・Schema が必要です。")
    if st.button("🚀 CREATE OR REPLACE TABLE してアップロード", type="primary", disabled=not can_run):
        with st.status(f"実行中... {table} を作り直してロードしています", expanded=True) as status:
            conn = None
            try:
                if ctx.session is None:
                    st.write("Snowflake に接続中...")
                    conn = connect_snowflake(ctx.cfg, ctx.db, ctx.schema)
                st.write(f"CREATE OR REPLACE TABLE {table} を実行中...")
                exec_sql(ddl, session=ctx.session, conn=conn)
                st.write(f"{len(df):,} 行をロード中...")
                load_dataframe(df, table, ctx.db, ctx.schema, session=ctx.session, conn=conn)
                rows = exec_sql(f"SELECT COUNT(*) AS N FROM {fqtn}", session=ctx.session, conn=conn)
                cnt = rows[0]["N"] if ctx.session is not None else rows[0][0]
                status.update(label=f"完了: {cnt:,} 行 → {table}", state="complete", expanded=False)
                st.success(f"完了: {len(df):,} 行 → `{fqtn}`")
            except Exception as e:  # noqa: BLE001
                status.update(label="アップロード失敗", state="error")
                st.error(f"アップロード失敗: {e}")
            finally:
                if conn is not None:
                    conn.close()


def _resolve_sheet_and_table(spec: DatasetSpec, xls: pd.ExcelFile):
    """シート名と出力テーブル名を決める。月別(実績)は selectbox、それ以外は固定。"""
    if spec.month_mode:
        months = [s for s in xls.sheet_names if re.match(r"^\d{4}\D?\d{2}", s)]
        if not months:
            st.error("月別シート（例: 2025.04）が見つかりません。")
            return None, None
        sheet = st.selectbox("シート（月）", months)
        return sheet, f"{spec.table}_{yyyymm(sheet)}"

    if spec.sheet not in xls.sheet_names:
        st.error(f"シート「{spec.sheet}」が見つかりません。シート一覧: {xls.sheet_names}")
        return None, None
    st.info(f"シートは「{spec.sheet}」に固定しています。")
    return spec.sheet, spec.table


def render_dataset(ctx: LoadContext, spec: DatasetSpec) -> None:
    """spec に従い、アップロード → 抽出 → 型変換 → プレビュー → ロードを描画する。"""
    if spec.caption:
        st.caption(spec.caption)
    uploaded = st.file_uploader("Excel (.xlsx)", type=["xlsx"], key=spec.label)
    if uploaded is None:
        st.info("Excel をアップロードしてください。")
        return

    xls = pd.ExcelFile(uploaded, engine="openpyxl")
    sheet, table = _resolve_sheet_and_table(spec, xls)
    if sheet is None:
        return
    fqtn = ".".join(x for x in [ctx.db, ctx.schema, table] if x)

    if spec.layout == "wide":
        fixed, date_names, data = wide_extract(
            xls, sheet, spec.header_row, spec.first_col, spec.fixed_n, spec.key_col)
        columns = fixed + date_names
    else:
        data = flat_extract(xls, sheet, spec.header_row, spec.key_col)
        fixed, date_names, columns = [], [], list(data.columns)

    def type_for(col: str) -> str:
        return spec.type_for(col, date_names)

    df = cast_by_type(data, type_for)
    ddl = build_ddl(fqtn, columns, type_for)

    st.subheader("プレビュー")
    if spec.layout == "wide":
        st.write(f"テーブル: **{fqtn}** ／ 固定列 {len(fixed)} ＋ **日付列 {len(date_names)}** ／ **{len(df):,} 行**")
        if date_names:
            st.caption(f"日付列: {date_names[0]} 〜 {date_names[-1]}")
    else:
        st.write(f"テーブル: **{fqtn}** ／ {len(columns)} 列 ／ **{len(df):,} 行**")
    st.dataframe(df.head(50), use_container_width=True)
    with st.expander("生成される DDL を確認"):
        st.code(ddl + ";", language="sql")
    if spec.note:
        st.caption(spec.note)

    st.divider()
    run_upload(ctx, table, fqtn, ddl, df)
