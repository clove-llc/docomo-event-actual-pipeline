"""BigQuery ↔ Snowflake 値突合ツール（厳密比較）

BQ→SF 移行の検証用。BigQuery 本番の source テーブルと、Snowflake 側で再現した
テーブルを **行レベル** で突合する。

DB 間の値表現の差は **Python（本ツール）側で巻き取って** 比較する:
  - num : float に統一（Decimal / Integer / Float の差を吸収。IEEE 表現ゆらぎ対策で小数9桁丸め）
  - date: date に統一（YYYY-MM-DD 文字列）
  - bool: bool に統一
  - str : trim しない（BQ も空白を保持）。空文字と NULL は両DBで NULL。
          **Excel エラー（#N/A 等）は NULL に揃える**（BQ=文字列 "#N/A" / SF=NULL。
          特に数式エラー由来の #N/A は pandas が保持できないため、ここで吸収する。
          ※ #N/A 行でも、値の入った他列はそのまま比較対象になる）。

既知の設計差は対象列から外して比較する（masking ではなく「比較しない列」を明示）:
  - 実績 source_sheet_name: SF=正規化 yyyymm（例 202510）/ BQ=生シート名（例 2025.1）。
    → 各テーブル定義の exclude に列挙し、理由を残す。

対象（既定）: レイヤー別に2系統を突合する。
  raw 層: BQ docomo_event_raw.raw_*     ↔ SF HARATO.RAW.RAW_*（源泉作成＝GAS独自実装が BQ raw と一致するか）
  stg 層: BQ docomo_event_staging.stg_* ↔ SF HARATO.STG.STG_*（BQ staging の passthrough / TRIM ミラー）
  各層とも: 人流デシル / 季節指数 / 実績データ（source_sheet_name 除外）/ 日付マスタ / 施設マスタ / 施設名マッピング

依存: google-cloud-bigquery, snowflake-connector-python, pandas

認証:
  - BigQuery: ADC（gcloud auth application-default login）。
  - Snowflake: 環境変数 SNOWFLAKE_ACCOUNT/USER/PRIVATE_KEY_PATH/ROLE/WAREHOUSE/DATABASE
    （dbt プロファイル dbt_project と同じ env_var）。

使い方:
  python tools/verify_code.py                  # 全レイヤー・全テーブル突合
  python tools/verify_code.py --layer raw      # raw 層のみ（源泉作成 ↔ BQ raw）
  python tools/verify_code.py --layer stg      # stg 層のみ（staging ↔ BQ staging）
  python tools/verify_code.py --table 季節指数  # ラベル指定（両レイヤー）
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
# レイヤー別の突合先 BQ データセット。
#   raw : BQ docomo_event_raw.raw_*            ↔ SF HARATO.RAW.RAW_*（源泉作成層＝GAS独自実装の再現）
#   stg : BQ docomo_event_staging.stg_*        ↔ SF HARATO.STG.STG_*（BQ staging のミラー）
BQ_RAW_DATASET = os.environ.get("BQ_RAW_DATASET", "docomo_event_raw")
BQ_STG_DATASET = os.environ.get("BQ_STG_DATASET", "docomo_event_staging")
NUM_ROUND = 9  # IEEE 浮動小数の表現ゆらぎを吸収する丸め桁（データ精度より十分細かい）
# Excel エラー（BQ は文字列保持・SF は NULL）。比較では NULL に揃えて吸収する。
EXCEL_ERRORS = {"#N/A", "#NAME?", "#REF!", "#VALUE!", "#DIV/0!", "#NUM!", "#NULL!"}

_FLAGS = ["gw", "obon", "three_day_holiday", "new_year", "regular_weekend",
          "year_end", "bridge_holiday", "weekday", "black_friday"]

# 列 → 論理型（突合対象列＝この dict のキー）
T_DECILE = {"facility_code": "num", "facility_name": "str",
            **{f"{f}_foot_traffic_avg": "num" for f in _FLAGS},
            **{f"{f}_decile_rank": "num" for f in _FLAGS}}
T_ZSCORE = {"date": "date", "facility_code": "num", "facility_name": "str",
            "z_score": "num", "month": "num", "week_number_monthly": "num", "date_flag": "str"}
T_ACTUALS = {"source_sheet_name": "str", "regional_office_name": "str", "branch_office_name": "str",
             "facility_name": "str", "floor_label": "str", "space_name": "str", "area_raw": "str",
             "helper_company_name": "str", "staff_count_raw": "str",
             "start_date": "date", "end_date": "date", "event_date": "date", "actual_value": "num"}
T_DATE_MASTER = {"date": "date", "year_month": "str", "year": "num", "month": "num", "day": "num",
                 "week_number_yearly": "num", "week_number_monthly": "num", "weekday_name": "str",
                 "weekday_name_and_week_number_monthly": "str", "weekday_holiday_weekend": "str",
                 "is_offday": "bool", "holiday_name": "str", "is_holiday": "bool",
                 "weekday_holiday_with_holiday": "str", "date_type": "str", "date_flag": "str"}
T_FACILITY_MASTER = {"facility_code": "num", "facility_name": "str", "po_level": "str",
                     "regional_office": "str", "branch_office": "str"}
T_NAME_MAPPINGS = {"original_name": "str", "mapped_name": "str"}

# (ラベル, レイヤー, BQデータセット, BQテーブル, SF FQTN, 列型, 除外列{列: 理由})
#   raw 層: SF 源泉作成（HARATO.RAW.RAW_*）が BQ raw と一致するか（独自実装 ↔ BQ raw データ）。
#   stg 層: SF staging（HARATO.STG.STG_*）が BQ staging と一致するか（passthrough / TRIM のミラー）。
_EXCL_ACTUALS = {"source_sheet_name": "SF=正規化yyyymm(202510) / BQ=生シート名(2025.1) の設計差"}
TABLES = [
    # --- raw 層（源泉作成 ↔ BQ raw）---
    ("人流デシル", "raw", BQ_RAW_DATASET, "raw_facility_foot_traffic_avg_and_decile_by_flag", "HARATO.RAW.RAW_FACILITY_FOOT_TRAFFIC_AVG_AND_DECILE_BY_FLAG", T_DECILE, {}),
    ("季節指数", "raw", BQ_RAW_DATASET, "raw_facility_daily_deviation_zscore", "HARATO.RAW.RAW_FACILITY_DAILY_DEVIATION_ZSCORE", T_ZSCORE, {}),
    ("実績データ", "raw", BQ_RAW_DATASET, "raw_facility_actuals", "HARATO.RAW.RAW_FACILITY_ACTUALS", T_ACTUALS, _EXCL_ACTUALS),
    ("日付マスタ", "raw", BQ_RAW_DATASET, "raw_date_master", "HARATO.RAW.RAW_DATE_MASTER", T_DATE_MASTER, {}),
    ("施設マスタ", "raw", BQ_RAW_DATASET, "raw_facility_master", "HARATO.RAW.RAW_FACILITY_MASTER", T_FACILITY_MASTER, {}),
    ("施設名マッピング", "raw", BQ_RAW_DATASET, "raw_facility_name_mappings", "HARATO.RAW.RAW_FACILITY_NAME_MAPPINGS", T_NAME_MAPPINGS, {}),
    # --- stg 層（staging ↔ BQ staging）---
    ("人流デシル", "stg", BQ_STG_DATASET, "stg_facility_foot_traffic_avg_and_decile_by_flag", "HARATO.STG.STG_FACILITY_FOOT_TRAFFIC_AVG_AND_DECILE_BY_FLAG", T_DECILE, {}),
    ("季節指数", "stg", BQ_STG_DATASET, "stg_facility_daily_deviation_zscore", "HARATO.STG.STG_FACILITY_DAILY_DEVIATION_ZSCORE", T_ZSCORE, {}),
    ("実績データ", "stg", BQ_STG_DATASET, "stg_facility_actuals", "HARATO.STG.STG_FACILITY_ACTUALS", T_ACTUALS, _EXCL_ACTUALS),
    ("日付マスタ", "stg", BQ_STG_DATASET, "stg_date_master", "HARATO.STG.STG_DATE_MASTER", T_DATE_MASTER, {}),
    ("施設マスタ", "stg", BQ_STG_DATASET, "stg_facility_master", "HARATO.STG.STG_FACILITY_MASTER", T_FACILITY_MASTER, {}),
    ("施設名マッピング", "stg", BQ_STG_DATASET, "stg_facility_name_mappings", "HARATO.STG.STG_FACILITY_NAME_MAPPINGS", T_NAME_MAPPINGS, {}),
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
        "database": os.environ.get("SNOWFLAKE_DATABASE", "HARATO"),
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
    ap.add_argument("--layer", choices=["raw", "stg"], help="レイヤー指定で絞り込み（raw / stg）")
    ap.add_argument("--show-diff", action="store_true", help="不一致行のサンプルを表示")
    args = ap.parse_args()

    bq = connect_bq()
    sf = connect_sf()
    print("=== BQ ↔ Snowflake 厳密突合（型統一のみ）===")
    results = []
    current_layer = None
    try:
        for label, layer, bq_dataset, bq_table, sf_fqtn, types, exclude in TABLES:
            if args.table and args.table != label:
                continue
            if args.layer and args.layer != layer:
                continue
            if layer != current_layer:
                current_layer = layer
                print(f"\n--- {layer} 層（BQ {bq_dataset} ↔ SF HARATO.{layer.upper()}）---")
            bq_df = bq_dataframe(bq, bq_dataset, bq_table, list(types))
            sf_df = sf_dataframe(sf, sf_fqtn)
            results.append(compare(f"{label}[{layer}]", bq_df, sf_df, types, exclude, args.show_diff))
    finally:
        sf.close()
    print("\n総合:", "★ 全テーブル一致" if all(results) else "差分あり")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
