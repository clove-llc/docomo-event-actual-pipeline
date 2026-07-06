"""BigQuery ↔ Snowflake 値突合ツール（厳密比較）

BQ→SF 移行の検証用。BigQuery 本番のテーブルと、Snowflake 側で再現した
テーブルを **行レベル** で突合する。

比較は **BigQuery の持つカラムベース** で行う:
  - 各テーブルの比較列は BQ INFORMATION_SCHEMA から自動導出する（手書き定義はしない）。
  - SF 側にしか無い列（拡張列）は比較対象外。SF に無い BQ 列は警告して除外する。

DB 間の値表現の差は **Python（本ツール）側で巻き取って** 比較する:
  - num : float に統一（Decimal / Integer / Float の差を吸収。IEEE 表現ゆらぎ対策で小数9桁丸め）
  - date: date に統一（YYYY-MM-DD 文字列）
  - bool: bool に統一
  - str : trim しない（BQ も空白を保持）。空文字と NULL は両DBで NULL。
          **Excel エラー（#N/A 等）は NULL に揃える**（BQ=文字列 "#N/A" / SF=NULL）。

既知の設計差は対象列から外して比較する（masking ではなく「比較しない列」を明示）:
  - source_sheet_name: SF=正規化 yyyymm（例 202510）/ BQ=生シート名（例 2025.1）。
  - branch_office    : SF=拠点略号プレフィックス除去（例 BQ「神）神奈川支店」→ SF「神奈川支店」）。

対象: レイヤー別に突合する（SF 側の実体配置に合わせる）。
  raw 層 : BQ docomo_event_raw.raw_*          ↔ SF HARATO.RAW.RAW_*
           （源泉作成層。実績はアップローダが横持ち RAW_FACILITY_ACTUALS_<yyyymm> を
             縦持ち化して RAW_FACILITY_ACTUALS を生成する。他は GAS 独自実装の再現）
  stg 層 : BQ docomo_event_staging.stg_*      ↔ SF DOCOMO_DB.STG.STG_*（view）
  int 層 : BQ docomo_event_intermediate.int_* ↔ SF DOCOMO_DB.INT.INT_*（view）
  mart 層: BQ docomo_event_mart.fact_*        ↔ SF DOCOMO_DB.MART.FACT_*（view）
  ※ SF 独自テーブル（STG_FACILITY_SCHEDULE_CONSTRAINTS_MASTER /
     STG_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER）は BQ に対応が無いため対象外。

依存: google-cloud-bigquery, snowflake-connector-python, pandas

認証:
  - BigQuery: ADC（gcloud auth application-default login）。
  - Snowflake: 環境変数 SNOWFLAKE_ACCOUNT/USER/PRIVATE_KEY_PATH/ROLE/WAREHOUSE
    （dbt プロファイル dbt_project と同じ env_var）。

使い方:
  python tools/verify_code.py                  # 全レイヤー・全テーブル突合
  python tools/verify_code.py --layer raw      # レイヤー指定
  python tools/verify_code.py --table 季節指数  # ラベル指定
  python tools/verify_code.py --show-diff      # 不一致行のサンプルを表示
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import math
import os
from collections import Counter

import pandas as pd

# ===== 設定 =====
BQ_PROJECT = os.environ.get("BQ_PROJECT", "digital-well-456700-i9")
BQ_RAW_DATASET = os.environ.get("BQ_RAW_DATASET", "docomo_event_raw")
BQ_STG_DATASET = os.environ.get("BQ_STG_DATASET", "docomo_event_staging")
BQ_INT_DATASET = os.environ.get("BQ_INT_DATASET", "docomo_event_intermediate")
BQ_MART_DATASET = os.environ.get("BQ_MART_DATASET", "docomo_event_mart")
# SF 側: raw はアップローダ出力先（HARATO.RAW）、stg/int/mart は dbt の view 層（DOCOMO_DB）
SF_RAW_DB = os.environ.get("SF_RAW_DB", "HARATO.RAW")
SF_DB = os.environ.get("SF_DB", "DOCOMO_DB")
NUM_ROUND = 9  # IEEE 浮動小数の表現ゆらぎを吸収する丸め桁（データ精度より十分細かい）
# Excel エラー（BQ は文字列保持・SF は NULL）。比較では NULL に揃えて吸収する。
EXCEL_ERRORS = {"#N/A", "#NAME?", "#REF!", "#VALUE!", "#DIV/0!", "#NUM!", "#NULL!"}

# 既知の設計差（比較しない列: 列名 → 理由）
_EXCL_SHEET = {"source_sheet_name": "SF=正規化yyyymm(202510) / BQ=生シート名(2025.1) の設計差"}
_EXCL_BRANCH = {"branch_office": "SF=拠点略号プレフィックス除去（神）神奈川支店→神奈川支店）の設計差"}
# mart is_excluded: BQ=除外マスタ未マッチ行はNULL / SF=FALSEに正規化。意味的に等価
# （TRUE 50,370行・23施設の集合一致をSQLで確認済み）。NULL⇔FALSE の表現差のため除外。
_EXCL_MART = {**_EXCL_BRANCH,
              "is_excluded": "BQ=NULL/SF=FALSE正規化の設計差（TRUE集合の一致は確認済み）"}

# (ラベル, レイヤー, BQデータセット, BQテーブル, SF FQTN, 除外列{列: 理由})
# 比較列は BQ INFORMATION_SCHEMA から自動導出（BQ カラムベース）。
TABLES = [
    # --- raw 層（BQ raw ↔ HARATO.RAW。実績はアップローダの縦持ち化出力）---
    ("人流デシル", "raw", BQ_RAW_DATASET, "raw_facility_foot_traffic_avg_and_decile_by_flag", f"{SF_RAW_DB}.RAW_FACILITY_FOOT_TRAFFIC_AVG_AND_DECILE_BY_FLAG", {}),
    ("季節指数", "raw", BQ_RAW_DATASET, "raw_facility_daily_deviation_zscore", f"{SF_RAW_DB}.RAW_FACILITY_DAILY_DEVIATION_ZSCORE", {}),
    ("実績データ", "raw", BQ_RAW_DATASET, "raw_facility_actuals", f"{SF_RAW_DB}.RAW_FACILITY_ACTUALS", _EXCL_SHEET),
    ("日付マスタ", "raw", BQ_RAW_DATASET, "raw_date_master", f"{SF_RAW_DB}.RAW_DATE_MASTER", {}),
    ("施設マスタ", "raw", BQ_RAW_DATASET, "raw_facility_master", f"{SF_RAW_DB}.RAW_FACILITY_MASTER", _EXCL_BRANCH),
    ("施設名マッピング", "raw", BQ_RAW_DATASET, "raw_facility_name_mappings", f"{SF_RAW_DB}.RAW_FACILITY_NAME_MAPPINGS", {}),
    ("除外施設マスタ", "raw", BQ_RAW_DATASET, "raw_excluded_facility_master", f"{SF_RAW_DB}.RAW_EXCLUDED_FACILITY_MASTER", {}),
    ("目標CPAマスタ", "raw", BQ_RAW_DATASET, "raw_facility_target_cpa_master", f"{SF_RAW_DB}.RAW_FACILITY_TARGET_CPA_MASTER", {}),
    # --- stg 層（BQ staging ↔ DOCOMO_DB.STG）---
    ("人流デシル", "stg", BQ_STG_DATASET, "stg_facility_foot_traffic_avg_and_decile_by_flag", f"{SF_DB}.STG.STG_FACILITY_FOOT_TRAFFIC_AVG_AND_DECILE_BY_FLAG", {}),
    ("季節指数", "stg", BQ_STG_DATASET, "stg_facility_daily_deviation_zscore", f"{SF_DB}.STG.STG_FACILITY_DAILY_DEVIATION_ZSCORE", {}),
    ("実績データ", "stg", BQ_STG_DATASET, "stg_facility_actuals", f"{SF_DB}.STG.STG_FACILITY_ACTUALS", _EXCL_SHEET),
    ("日付マスタ", "stg", BQ_STG_DATASET, "stg_date_master", f"{SF_DB}.STG.STG_DATE_MASTER", {}),
    ("施設マスタ", "stg", BQ_STG_DATASET, "stg_facility_master", f"{SF_DB}.STG.STG_FACILITY_MASTER", _EXCL_BRANCH),
    ("施設名マッピング", "stg", BQ_STG_DATASET, "stg_facility_name_mappings", f"{SF_DB}.STG.STG_FACILITY_NAME_MAPPINGS", {}),
    ("除外施設マスタ", "stg", BQ_STG_DATASET, "stg_excluded_facility_master", f"{SF_DB}.STG.STG_EXCLUDED_FACILITY_MASTER", {}),
    ("目標CPAマスタ", "stg", BQ_STG_DATASET, "stg_facility_target_cpa_master", f"{SF_DB}.STG.STG_FACILITY_TARGET_CPA_MASTER", {}),
    # --- int 層（BQ intermediate ↔ DOCOMO_DB.INT）---
    ("実績(int)", "int", BQ_INT_DATASET, "int_facility_actuals", f"{SF_DB}.INT.INT_FACILITY_ACTUALS", _EXCL_SHEET),
    ("日別実績", "int", BQ_INT_DATASET, "int_facility_daily_actual", f"{SF_DB}.INT.INT_FACILITY_DAILY_ACTUAL", _EXCL_BRANCH),
    ("ベンチ期間", "int", BQ_INT_DATASET, "int_benchmark_periods", f"{SF_DB}.INT.INT_BENCHMARK_PERIODS", {}),
    ("デシルマッピング", "int", BQ_INT_DATASET, "int_facility_event_decile_mapping", f"{SF_DB}.INT.INT_FACILITY_EVENT_DECILE_MAPPING", {}),
    ("デシル平均実績", "int", BQ_INT_DATASET, "int_facility_event_decile_avg_actual", f"{SF_DB}.INT.INT_FACILITY_EVENT_DECILE_AVG_ACTUAL", _EXCL_BRANCH),
    ("デシルベンチ", "int", BQ_INT_DATASET, "int_event_decile_benchmark", f"{SF_DB}.INT.INT_EVENT_DECILE_BENCHMARK", {}),
    ("月週フラグZ", "int", BQ_INT_DATASET, "int_facility_monthly_weekday_dateflag_deviation_zscore", f"{SF_DB}.INT.INT_FACILITY_MONTHLY_WEEKDAY_DATEFLAG_DEVIATION_ZSCORE", {}),
    ("月フラグZ", "int", BQ_INT_DATASET, "int_facility_monthly_dateflag_deviation_zscore", f"{SF_DB}.INT.INT_FACILITY_MONTHLY_DATEFLAG_DEVIATION_ZSCORE", {}),
    ("計画スナップショット", "int", BQ_INT_DATASET, "int_facility_event_planning_snapshot", f"{SF_DB}.INT.INT_FACILITY_EVENT_PLANNING_SNAPSHOT", _EXCL_BRANCH),
    ("施設別目標CPA", "int", BQ_INT_DATASET, "int_facility_target_cpa_by_facility", f"{SF_DB}.INT.INT_FACILITY_TARGET_CPA_BY_FACILITY", {}),
    # --- mart 層（BQ mart ↔ DOCOMO_DB.MART）---
    ("実績スロットFact", "mart", BQ_MART_DATASET, "fact_facility_performance_slots", f"{SF_DB}.MART.FACT_FACILITY_PERFORMANCE_SLOTS", _EXCL_MART),
]


# ===== 正規化（型表現の統一のみ。値の中身は変えない）=====
def normalize(value, coltype: str):
    try:
        if value is None or pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if coltype == "date":
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime("%Y-%m-%d")
        return str(value)[:10]
    if coltype == "num":
        f = float(value)
        return None if math.isnan(f) else round(f, NUM_ROUND)
    if coltype == "bool":
        return bool(value)
    s = str(value)  # str は trim しない。Excel エラーのみ NULL に吸収する
    return None if s in EXCEL_ERRORS else s


def to_multiset(df: pd.DataFrame, cols: list[str], types: dict) -> Counter:
    return Counter(
        tuple(normalize(df.iloc[i][c], types[c]) for c in cols)
        for i in range(len(df))
    )


def multiset_hash(counter: Counter) -> str:
    """正規化後の多重集合を順序非依存にハッシュ（行と出現回数をソート連結→MD5）。"""
    items = sorted(f"{row!r}|{cnt}" for row, cnt in counter.items())
    return hashlib.md5("\n".join(items).encode("utf-8")).hexdigest()


# ===== データ取得 =====
def _bq_logical_type(bq_type: str) -> str:
    """BigQuery のデータ型 → 突合用の論理型（num/date/bool/str）。"""
    t = (bq_type or "").upper().split("(")[0]
    if t in ("INT64", "INTEGER", "NUMERIC", "BIGNUMERIC", "FLOAT64", "FLOAT", "DECIMAL"):
        return "num"
    if t == "DATE":
        return "date"
    if t in ("BOOL", "BOOLEAN"):
        return "bool"
    return "str"  # STRING / DATETIME / TIMESTAMP 等は文字列扱いで比較


def bq_column_types(client, dataset: str, table: str) -> dict:
    """BQ INFORMATION_SCHEMA から {列名(小文字): 論理型} を作る（BQ カラムベースの源）。"""
    sql = (f"SELECT column_name, data_type FROM `{BQ_PROJECT}.{dataset}.INFORMATION_SCHEMA.COLUMNS` "
           f"WHERE table_name = '{table}' ORDER BY ordinal_position")
    return {r["column_name"].lower(): _bq_logical_type(r["data_type"]) for r in client.query(sql).result()}


def bq_dataframe(client, dataset: str, table: str, cols: list[str]) -> pd.DataFrame:
    sql = f"SELECT {', '.join(cols)} FROM `{BQ_PROJECT}.{dataset}.{table}`"
    rows = list(client.query(sql).result())
    return pd.DataFrame([{c: r[c] for c in cols} for r in rows], columns=cols)


def sf_dataframe(conn, fqtn: str) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {fqtn}")
    names = [d[0].lower() for d in cur.description]
    data = cur.fetchall()
    cur.close()
    return pd.DataFrame(data, columns=names)


def connect_bq():
    from google.cloud import bigquery
    return bigquery.Client(project=BQ_PROJECT)


def connect_sf():
    import snowflake.connector
    params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "role": os.environ.get("SNOWFLAKE_ROLE"),
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE"),
        "private_key_file": os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH"),
    }
    return snowflake.connector.connect(**{k: v for k, v in params.items() if v})


# ===== 突合 =====
def compare(label, bq_df, sf_df, types, exclude, show_diff=False) -> bool:
    cols = [c for c in types if c not in exclude]
    cb = to_multiset(bq_df, cols, types)
    cs = to_multiset(sf_df, cols, types)
    only_bq, only_sf = cb - cs, cs - cb
    matched = sum((cb & cs).values())
    ok = sum(only_bq.values()) == 0 and sum(only_sf.values()) == 0
    hb, hs = multiset_hash(cb), multiset_hash(cs)
    excl = f" 除外列={list(exclude)}" if exclude else ""
    print(f"{label:16} BQ={sum(cb.values()):>7} SF={sum(cs.values()):>7} 一致={matched:>7} "
          f"BQのみ={sum(only_bq.values()):>4} SFのみ={sum(only_sf.values()):>4}  "
          f"{'OK 一致' if ok else 'X 差分'}{excl}")
    print(f"{'':16} hash BQ={hb} SF={hs} {'(一致)' if hb == hs else '(不一致)'}")
    if show_diff and not ok:
        for t, _ in list(only_bq.items())[:5]:
            print("   BQのみ:", dict(zip(cols, t)))
        for t, _ in list(only_sf.items())[:5]:
            print("   SFのみ:", dict(zip(cols, t)))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", help="ラベル指定で1テーブルのみ突合")
    ap.add_argument("--layer", choices=["raw", "stg", "int", "mart"], help="レイヤー指定で絞り込み")
    ap.add_argument("--show-diff", action="store_true", help="不一致行のサンプルを表示")
    args = ap.parse_args()

    bq = connect_bq()
    sf = connect_sf()
    print("=== BQ ↔ Snowflake 厳密突合（BQカラムベース・型統一のみ）===")
    results = []
    current_layer = None
    try:
        for label, layer, bq_dataset, bq_table, sf_fqtn, exclude in TABLES:
            if args.table and args.table != label:
                continue
            if args.layer and args.layer != layer:
                continue
            if layer != current_layer:
                current_layer = layer
                sf_loc = SF_RAW_DB if layer == "raw" else f"{SF_DB}.{layer.upper()}"
                print(f"\n--- {layer} 層（BQ {bq_dataset} ↔ SF {sf_loc}）---")
            # 比較列は BQ schema から自動導出（BQ カラムベース）
            types = bq_column_types(bq, bq_dataset, bq_table)
            sf_df = sf_dataframe(sf, sf_fqtn)
            sf_cols = set(sf_df.columns)
            common = {c: t for c, t in types.items() if c in sf_cols}
            dropped = [c for c in types if c not in sf_cols]
            if dropped:
                print(f"   [警告] {label}[{layer}] SFに無いBQ列を比較除外: {dropped}")
            bq_df = bq_dataframe(bq, bq_dataset, bq_table, list(common))
            results.append(compare(f"{label}[{layer}]", bq_df, sf_df, common, exclude, args.show_diff))
    finally:
        sf.close()
    print("\n総合:", "★ 全テーブル一致" if all(results) else "差分あり")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
