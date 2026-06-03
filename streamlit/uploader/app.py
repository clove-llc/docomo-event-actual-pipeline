"""実績データ（横持ち）アップローダ → raw_facility_actuals_<yyyymm>

実績データ.xlsx の月別シートを、横持ちのまま Snowflake にロードする。
- ヘッダーは4行目（0始まりで index 3）、A列は空。
- 固定13列（No〜実施日数）は日本語名そのまま。
- 日付列はシートごとに本数が変わるため**動的に取得**（列名は "YYYY-MM-DD"）。
- アップロード時に `CREATE OR REPLACE TABLE raw_facility_actuals_<yyyymm>` して都度作り直す。

列の型（rawは原文保持を基本とし、確実な列のみ型付け）:
- No → NUMBER / 開始日・終了日 → DATE / 日付列 → NUMBER
- 面積・スタッフ数・実施日数 は表記が混在（単位・範囲・「N日間」・Excel日付化）するため VARCHAR
- その他の固定列（実施月/支社名/支店/施設名/フロア/スペース名/ヘルパー会社）→ VARCHAR

起動（ローカル）:
    cd streamlit/uploader
    pip install -r requirements.txt
    streamlit run app.py

デプロイ（SiSへ更新）:
    ./deploy.sh
"""

from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from sf_common import (connect_snowflake, current_db_schema, exec_sql,
                       get_active_session, get_sf_config, load_dataframe)

HEADER_ROW = 3   # 0始まり：4行目がヘッダー
FIRST_COL = 1    # A列(0)は空。B列(1)から
FIXED_N = 13     # No〜実施日数

# 固定列の型（未掲載の列は VARCHAR）
FIXED_TYPES = {
    "No": "NUMBER(38,0)",
    "面積": "VARCHAR",
    "スタッフ数": "VARCHAR",
    "開始日": "DATE",
    "終了日": "DATE",
    "実施日数": "VARCHAR",
}
DATE_COL_TYPE = "NUMBER(38,0)"   # 動的な日付列（日次の人数等）
NUMERIC_FIXED = {"No"}
DATE_FIXED = {"開始日", "終了日"}

# 監査列：ロード（CREATE OR REPLACE）時刻を記録
AUDIT_COL = "latest_updated_at"
AUDIT_DDL = f'  "{AUDIT_COL}" TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()'

# 日付列の値正規化（既存 GAS / Python と同じ）: ＠/@/中止/確認中/不明→NULL、なし→0、カンマ除去
NULL_TOKENS = {"＠", "@", "中止", "確認中", "不明"}
ZERO_TOKENS = {"なし"}

st.set_page_config(page_title="実績データ アップロード", page_icon="📈", layout="wide")
st.title("📈 実績データ アップロード")
st.caption("月別シートを横持ちのまま、シートごとに CREATE OR REPLACE TABLE してロード")


def yyyymm(sheet: str) -> str:
    """シート名の先頭から年(4桁)＋月を取り、YYYYMM を返す（例: '2025.11（更新済）' → '202511'）。"""
    m = re.match(r"\s*(\d{4})\D*(\d{1,2})", sheet)
    if m:
        return m.group(1) + m.group(2).zfill(2)
    return re.sub(r"\D", "", sheet)[:6]


def fixed_type(name: str) -> str:
    return FIXED_TYPES.get(name, "VARCHAR")


def extract_wide(xls: pd.ExcelFile, sheet: str):
    """シートから 固定列名・日付列名(ISO)・データ(全str/None) を取り出す。"""
    header = pd.read_excel(xls, sheet_name=sheet, header=None,
                           nrows=HEADER_ROW + 1, engine="openpyxl").iloc[HEADER_ROW]
    data = pd.read_excel(xls, sheet_name=sheet, header=None,
                         skiprows=HEADER_ROW + 1, dtype=str, engine="openpyxl")

    header = header.iloc[FIRST_COL:].reset_index(drop=True)
    data = data.iloc[:, FIRST_COL:].reset_index(drop=True)

    fixed = [str(header.iloc[i]).strip() for i in range(FIXED_N)]
    date_names, date_idx = [], []
    for j in range(FIXED_N, len(header)):
        d = pd.to_datetime(header.iloc[j], errors="coerce")
        if pd.notna(d):
            date_names.append(d.strftime("%Y-%m-%d"))
            date_idx.append(j)

    data = data.iloc[:, list(range(FIXED_N)) + date_idx]
    data.columns = fixed + date_names

    # 施設名が空の行（注記・末尾の空行など）は除外
    if "施設名" in data.columns:
        data = data[data["施設名"].notna() & (data["施設名"].astype(str).str.strip() != "")]
    data = data.where(pd.notna(data), None).reset_index(drop=True)
    return fixed, date_names, data


def normalize_count(s: pd.Series) -> pd.Series:
    """日付列の値を既存GAS/Pythonと同じ規則で数値化する。

    ＠/@/中止/確認中/不明 → NULL、なし → 0、カンマ除去、その他の非数値 → NULL。
    """
    def conv(v):
        if v is None:
            return None
        t = str(v).strip()
        if t == "" or t in NULL_TOKENS:
            return None
        if t in ZERO_TOKENS:
            return 0
        n = pd.to_numeric(t.replace(",", "").replace("，", ""), errors="coerce")
        return None if pd.isna(n) else n
    return pd.to_numeric(s.map(conv), errors="coerce")


def cast_for_load(data: pd.DataFrame, fixed: list[str], date_names: list[str]) -> pd.DataFrame:
    """DDLの型に合わせて変換。日付列はGAS同等の正規化、VARCHAR列は原文のまま。"""
    out = data.copy()
    for c in fixed:
        if c in DATE_FIXED:
            # DATE列は YYYY-MM-DD 文字列にする（datetime64[ns]のまま渡すと Snowflake で variant→DATE 変換に失敗）
            d = pd.to_datetime(out[c], errors="coerce")
            out[c] = d.dt.strftime("%Y-%m-%d").where(d.notna(), None)
        elif c in NUMERIC_FIXED:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in date_names:
        out[c] = normalize_count(out[c])
    return out


def build_ddl(fqtn: str, fixed: list[str], date_names: list[str]) -> str:
    cols = [f'  "{c}" {fixed_type(c)}' for c in fixed]
    cols += [f'  "{d}" {DATE_COL_TYPE}' for d in date_names]
    cols.append(AUDIT_DDL)
    return f"CREATE OR REPLACE TABLE {fqtn} (\n" + ",\n".join(cols) + "\n)"


def token_report(data: pd.DataFrame, date_names: list[str]) -> list[tuple[str, str]]:
    """日付列に含まれる非数値トークンと、取込時の変換結果（参考表示用）。"""
    tokens = set()
    for c in date_names:
        for v in data[c].dropna().astype(str).str.strip().unique():
            if v == "":
                continue
            if pd.isna(pd.to_numeric(v.replace(",", "").replace("，", ""), errors="coerce")):
                tokens.add(v)
    rows = []
    for t in sorted(tokens):
        if t in ZERO_TOKENS:
            rows.append((t, "0"))
        elif t in NULL_TOKENS:
            rows.append((t, "NULL"))
        else:
            rows.append((t, "NULL（未知トークン）"))
    return rows


# ===== 接続環境 =====
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


# ===== アップロード =====
uploaded = st.file_uploader("実績データ.xlsx", type=["xlsx"])
if uploaded is None:
    st.info("実績データ.xlsx をアップロードしてください。")
    st.stop()

xls = pd.ExcelFile(uploaded, engine="openpyxl")
month_sheets = [s for s in xls.sheet_names if re.match(r"^\d{4}\D?\d{2}", s)]
if not month_sheets:
    st.error("月別シート（例: 2025.04）が見つかりません。")
    st.stop()

sheet = st.selectbox("シート（月）", month_sheets)
fixed, date_names, data = extract_wide(xls, sheet)
df = cast_for_load(data, fixed, date_names)
table = f"RAW_FACILITY_ACTUALS_{yyyymm(sheet)}"
fqtn = ".".join(x for x in [db, schema, table] if x)

st.subheader("プレビュー")
st.write(f"テーブル: **{fqtn}** ／ 固定列 {len(fixed)} ＋ **日付列 {len(date_names)}（動的）** ／ **{len(df):,} 行**")
st.caption(f"日付列: {date_names[0]} 〜 {date_names[-1]}" if date_names else "日付列なし")
st.dataframe(df.head(50), use_container_width=True)

with st.expander("生成される DDL を確認"):
    st.code(build_ddl(fqtn, fixed, date_names) + ";", language="sql")

# 日付列の非数値トークンの扱い（既存GASと同じ正規化。透明性のため表示）
report = token_report(data, date_names)
if report:
    with st.expander(f"日付列の非数値の扱い（{len(report)}種）— 既存GASと同じ正規化"):
        st.caption("＠/@/中止/確認中/不明 → NULL、なし → 0（カンマ除去のうえ数値化）")
        st.table(pd.DataFrame(report, columns=["値", "取込時の変換"]))

# ===== 実行 =====
st.divider()
can_run = (session is not None or bool(cfg)) and bool(db) and bool(schema)
if not can_run:
    st.info("※ 認証情報・Database・Schema が必要です。")

if st.button("🚀 CREATE OR REPLACE TABLE してアップロード", type="primary", disabled=not can_run):
    with st.status(f"実行中... {table} を作り直してロードしています", expanded=True) as status:
        conn = None
        try:
            if session is None:
                st.write("Snowflake に接続中...")
                conn = connect_snowflake(cfg, db, schema)
            st.write(f"CREATE OR REPLACE TABLE {table} を実行中...")
            exec_sql(build_ddl(fqtn, fixed, date_names), session=session, conn=conn)
            st.write(f"{len(df):,} 行をロード中...")
            load_dataframe(df, table, db, schema, session=session, conn=conn)
            rows = exec_sql(f"SELECT COUNT(*) AS N FROM {fqtn}", session=session, conn=conn)
            cnt = rows[0]["N"] if session is not None else rows[0][0]
            st.write(f"確認: COUNT(*) = {cnt:,}")
            status.update(label=f"完了: {cnt:,} 行 → {table}（{len(date_names)} 日付列）",
                          state="complete", expanded=False)
            st.success(f"完了: {len(df):,} 行 → `{fqtn}`（{len(date_names)} 日付列）")
        except Exception as e:  # noqa: BLE001
            status.update(label="アップロード失敗", state="error")
            st.error(f"アップロード失敗: {e}")
        finally:
            if conn is not None:
                conn.close()
