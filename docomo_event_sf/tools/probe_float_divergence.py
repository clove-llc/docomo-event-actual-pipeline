"""BigQuery ↔ Snowflake FLOAT 乖離プローブ（丸め前の生値を比較）

verify_code.py は NUM_ROUND=9 で丸めて突合するため、IEEE754 の最終ビット差
（ULPレベルの乖離）は見えない。本ツールは round_bq を外した生の集計値を
両エンジンで計算し、キー結合して以下を測る:

  - |BQ - SF|        : 絶対差（生値）
  - ULP距離          : double 何刻み離れているか（隣接doubleなら1）
  - 相対差           : |BQ - SF| / max(|BQ|, |SF|)

これにより「源泉(z_score)の生値がそもそも一致しているか」と
「集計(AVG/PERCENTILE)が何ULP乖離するか」を切り分ける。

認証は verify_code.py と同一（BQ=ADC / SF=SNOWFLAKE_* 環境変数）。

使い方:
  python tools/probe_float_divergence.py            # 全チェック
  python tools/probe_float_divergence.py --check zscore_src
"""
from __future__ import annotations

import argparse
import os
import struct

import pandas as pd

BQ_PROJECT = os.environ.get("BQ_PROJECT", "digital-well-456700-i9")
BQ_STG = os.environ.get("BQ_STG_DATASET", "docomo_event_staging")
BQ_INT = os.environ.get("BQ_INT_DATASET", "docomo_event_intermediate")

# ===== チェック定義 =====
# 各チェック: key（結合キー列）, val（比較する生float列）, bq_sql, sf_sql
# SQL は round を一切かけない（生の double を取得する）。
CHECKS = {
    # 源泉 z_score の生値（集計なし）。SF raw は GAS 独自実装 ＝ 一致するかを最初に確認。
    "zscore_src": {
        "desc": "源泉 z_score 生値（stg, 集計なし）",
        "key": ["date", "facility_code"],
        "val": "z_score",
        "bq": f"SELECT date, facility_code, z_score FROM `{BQ_PROJECT}.{BQ_STG}.stg_facility_daily_deviation_zscore`",
        "sf": "SELECT date, facility_code, z_score FROM HARATO.STG.STG_FACILITY_DAILY_DEVIATION_ZSCORE",
    },
    # 月週フラグZ: AVG(z_score) の生値（round_bq を外した版）。
    "avg_zscore_mw": {
        "desc": "月週フラグZ AVG(z_score) 生値",
        "key": ["facility_code", "month", "week_number_monthly", "date_flag"],
        "val": "v",
        "bq": f"""SELECT facility_code, month, week_number_monthly, date_flag, AVG(z_score) AS v
                  FROM `{BQ_PROJECT}.{BQ_STG}.stg_facility_daily_deviation_zscore`
                  GROUP BY facility_code, month, week_number_monthly, date_flag""",
        "sf": """SELECT facility_code, month, week_number_monthly, date_flag, AVG(z_score) AS v
                 FROM HARATO.STG.STG_FACILITY_DAILY_DEVIATION_ZSCORE
                 GROUP BY facility_code, month, week_number_monthly, date_flag""",
    },
    # 月フラグZ: AVG(AVG(z_score)) の生値（週平均をさらに平均。二段集計の乖離）。
    "avg_zscore_m": {
        "desc": "月フラグZ AVG(週平均) 生値（二段集計）",
        "key": ["facility_code", "month", "date_flag"],
        "val": "v",
        "bq": f"""SELECT facility_code, month, date_flag, AVG(wk) AS v FROM (
                    SELECT facility_code, month, week_number_monthly, date_flag, AVG(z_score) AS wk
                    FROM `{BQ_PROJECT}.{BQ_STG}.stg_facility_daily_deviation_zscore`
                    GROUP BY facility_code, month, week_number_monthly, date_flag)
                  GROUP BY facility_code, month, date_flag""",
        "sf": """SELECT facility_code, month, date_flag, AVG(wk) AS v FROM (
                    SELECT facility_code, month, week_number_monthly, date_flag, AVG(z_score) AS wk
                    FROM HARATO.STG.STG_FACILITY_DAILY_DEVIATION_ZSCORE
                    GROUP BY facility_code, month, week_number_monthly, date_flag)
                 GROUP BY facility_code, month, date_flag""",
    },
    # デシル平均実績: AVG(CAST(actual AS FLOAT)) の生値（デプロイ済み int 入力テーブルから再集計）。
    "avg_actual": {
        "desc": "デシル平均実績 AVG(actual) 生値",
        "key": ["benchmark_period_key", "facility_code", "date_flag", "decile_rank"],
        "val": "v",
        "bq": f"""SELECT p.benchmark_period_key, d.facility_code, d.date_flag, m.decile_rank,
                         AVG(CAST(d.actual AS FLOAT64)) AS v
                  FROM `{BQ_PROJECT}.{BQ_INT}.int_facility_daily_actual` d
                  JOIN `{BQ_PROJECT}.{BQ_INT}.int_benchmark_periods` p
                    ON d.date BETWEEN p.period_start_date AND p.period_end_date
                  LEFT JOIN `{BQ_PROJECT}.{BQ_INT}.int_facility_event_decile_mapping` m
                    ON d.facility_code = m.facility_code AND d.date_flag = m.date_flag
                  GROUP BY 1,2,3,4""",
        "sf": """SELECT p.benchmark_period_key, d.facility_code, d.date_flag, m.decile_rank,
                        AVG(CAST(d.actual AS FLOAT)) AS v
                 FROM HARATO.INT.INT_FACILITY_DAILY_ACTUAL d
                 JOIN HARATO.INT.INT_BENCHMARK_PERIODS p
                   ON d.date BETWEEN p.period_start_date AND p.period_end_date
                 LEFT JOIN HARATO.INT.INT_FACILITY_EVENT_DECILE_MAPPING m
                   ON d.facility_code = m.facility_code AND d.date_flag = m.date_flag
                 GROUP BY 1,2,3,4""",
    },
}


# ===== ULP距離（double 何刻み離れているか）=====
def _ordered(x: float) -> int:
    """double を単調順序の int に変換（同符号・近接値の ULP 差を正しく測るため）。"""
    i = struct.unpack("<q", struct.pack("<d", x))[0]
    return i if i >= 0 else 0x8000000000000000 - i


def ulp_distance(a: float, b: float) -> int:
    return abs(_ordered(a) - _ordered(b))


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


def _norm_key(df: pd.DataFrame, key: list[str]) -> pd.DataFrame:
    """キー列を文字列正規化（date/数値の型表現差を吸収して結合できるように）。"""
    for k in key:
        df[k] = df[k].map(lambda v: None if v is None else str(v)[:10] if "date" in k else str(v))
    return df


def run_check(bq, sf, name: str, spec: dict) -> None:
    bq_df = bq.query(spec["bq"]).result().to_dataframe()
    cur = sf.cursor()
    cur.execute(spec["sf"])
    sf_df = pd.DataFrame(cur.fetchall(), columns=[d[0].lower() for d in cur.description])
    cur.close()

    key, val = spec["key"], spec["val"]
    bq_df.columns = [c.lower() for c in bq_df.columns]
    sf_df.columns = [c.lower() for c in sf_df.columns]
    bq_df = _norm_key(bq_df, key)[key + [val]].rename(columns={val: "bq"})
    sf_df = _norm_key(sf_df, key)[key + [val]].rename(columns={val: "sf"})

    m = bq_df.merge(sf_df, on=key, how="inner")
    m = m.dropna(subset=["bq", "sf"])
    m["bq"] = m["bq"].astype(float)
    m["sf"] = m["sf"].astype(float)
    m["absdiff"] = (m["bq"] - m["sf"]).abs()
    m["ulp"] = [ulp_distance(a, b) for a, b in zip(m["bq"], m["sf"])]
    denom = m[["bq", "sf"]].abs().max(axis=1).replace(0, float("nan"))
    m["rel"] = m["absdiff"] / denom

    n = len(m)
    diff = m[m["absdiff"] > 0]
    nd = len(diff)
    print(f"\n■ {name}: {spec['desc']}")
    if not n:
        print("  結合行=0")
        return
    print(f"  結合行数={n:,}  完全一致={n - nd:,}  生値が違う={nd:,}  ({nd / n * 100:.3f}%)")

    def stat(s):  # 平均・最大・最小・中央 を1行に
        return f"平均={s.mean():.6g}  最大={s.max():.6g}  最小={s.min():.6g}  中央={s.median():.6g}"

    # 各エンジンの生値そのものの分布（Snowflake / BigQuery）
    print(f"  Snowflake : {stat(m['sf'])}")
    print(f"  BigQuery  : {stat(m['bq'])}")
    # BQ−SF の符号付き差分（平均/最大/最小/中央）
    signed = m["bq"] - m["sf"]
    print(f"  差分(BQ-SF): {stat(signed)}")
    if nd:
        print(f"  |差分| 絶対値: {stat(diff['absdiff'])}")
        print(f"  ULP距離      : 最大={int(diff['ulp'].max())}  中央={int(diff['ulp'].median())}  "
              f"分布={ {int(k_): int(v_) for k_, v_ in diff['ulp'].value_counts().sort_index().head(8).items()} }")
        print(f"  相対差       : {stat(diff['rel'])}")
        ex = diff.nlargest(3, "ulp")
        for _, r in ex.iterrows():
            k = {c: r[c] for c in key}
            print(f"    例 ulp={int(r['ulp'])}: BQ={r['bq']!r} SF={r['sf']!r} key={k}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", choices=list(CHECKS), help="特定チェックのみ実行")
    args = ap.parse_args()
    bq, sf = connect_bq(), connect_sf()
    print("=== BQ ↔ Snowflake FLOAT 乖離プローブ（生値・丸め前）===")
    try:
        for name, spec in CHECKS.items():
            if args.check and args.check != name:
                continue
            run_check(bq, sf, name, spec)
    finally:
        sf.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
