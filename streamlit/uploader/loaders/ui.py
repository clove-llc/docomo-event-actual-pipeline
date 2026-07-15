"""Streamlit UI（spec 駆動の汎用 render とロード実行）。"""

from __future__ import annotations

import re
from pathlib import Path
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

CREATE_RAW_FACILITY_ACTUALS_SQL_FILE = Path(__file__).parent.parent / "sql" / "create_raw_facility_actuals.sql"

def create_raw_facility_actuals(ctx: LoadContext, conn=None) -> int:
    sql = CREATE_RAW_FACILITY_ACTUALS_SQL_FILE.read_text(encoding="utf-8")

    exec_sql(
        sql,
        session=ctx.session,
        conn=conn,
    )

    fqtn = ".".join(x for x in [ctx.db, ctx.schema, "RAW_FACILITY_ACTUALS"] if x)

    rows = exec_sql(
        f"SELECT COUNT(*) AS N FROM {fqtn}",
        session=ctx.session,
        conn=conn,
    )

    return rows[0]["N"] if ctx.session is not None else rows[0][0]


def run_upload(ctx: LoadContext, table: str, fqtn: str, ddl: str, df: pd.DataFrame, month_mode: bool) -> None:
    """CREATE OR REPLACE TABLE → ロード（進捗を表示）。"""
    can_run = (ctx.session is not None or bool(ctx.cfg)) and bool(ctx.db) and bool(ctx.schema)
    if not can_run:
        st.info("※ 認証情報・Database・Schema が必要です。")
    if st.button("🚀 CREATE OR REPLACE TABLE してアップロード", type="primary", disabled=not can_run):
        progress = st.empty()

        conn = None
        try:
            if ctx.session is None:
                progress.info("Snowflake に接続中...")
                conn = connect_snowflake(ctx.cfg, ctx.db, ctx.schema)
                progress.empty()

            progress.info(f"CREATE OR REPLACE TABLE {table} を実行中...")
            exec_sql(ddl, session=ctx.session, conn=conn)
            progress.empty()

            progress.info(f"{len(df):,} 行をロード中...")
            load_dataframe(df, table, ctx.db, ctx.schema, session=ctx.session, conn=conn)
            progress.empty()

            rows = exec_sql(f"SELECT COUNT(*) AS N FROM {fqtn}", session=ctx.session, conn=conn)
            cnt = rows[0]["N"] if ctx.session is not None else rows[0][0]

            if month_mode:
                st.success(f"月次テーブルの作成完了: {cnt:,} 行 → {table}")

                try:
                    progress.info("統合テーブルを作成中...")
                    actuals_count = create_raw_facility_actuals(ctx, conn=conn)
                    progress.empty()

                    st.success(f"統合テーブルの作成完了: {actuals_count:,} 行 → RAW_FACILITY_ACTUALS")
                except Exception as e:
                    progress.empty()
                    st.warning(f"月次テーブルの作成は完了。統合テーブルの作成のみ失敗: {e}")
            else:
                st.success(f"ロード完了: {cnt:,} 行 → {table}")

        except Exception as e:  # noqa: BLE001
            progress.empty()
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
        data = flat_extract(xls, sheet, spec.header_row, spec.key_col, spec.rename, spec.usecols)
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
    run_upload(ctx, table, fqtn, ddl, df, spec.month_mode)
