"""1テーブルをBigQueryへ読み取り(SELECT)のみでプロファイルし、Markdownを出力する。

フェーズ:
  Phase1 情報収集     : 行数/サイズ/種別/作成・更新時刻/更新頻度、カラム一覧・型
  Phase2 基本統計     : カラムごとの NULL率/一意率/カーディナリティ/数値統計/日付範囲/区分値
  Phase3 セグメント別 : 低カーディナリティ列を軸に、件数・割合と他列のNULL率差を比較
  Phase4 品質チェック : 重複/エラー値/外れ値(IQR)/負値/日付の連続性・逆転

【厳守】BigQueryへの書き込み・変更・削除は一切行わない。実行するのは SELECT のみ。
        run() が SELECT/WITH 以外のクエリを拒否する二重の安全装置を持つ。

使い方:
  python profile_table.py --project P --dataset D --table T [--out FILE]
"""

import argparse
import json
import os

from google.cloud import bigquery

# 誤入力されがちなスプレッドシート由来のエラー値・センチネル
SENTINELS = ["#N/A", "#REF!", "#VALUE!", "#NAME?", "#DIV/0!", "NULL", "NA",
             "N/A", "-", "--", "なし", "未定", "未入力", "確認中", "@", "＠"]

NUMERIC_TYPES = {"INT64", "INTEGER", "FLOAT64", "FLOAT", "NUMERIC", "BIGNUMERIC"}
DATE_TYPES = {"DATE", "DATETIME", "TIMESTAMP"}


def is_measure_col(name):
    """外れ値判定の対象とする「量的指標」らしい列か（ID/コード/区分/時間軸は除外）。"""
    c = name.lower()
    if any(c.endswith(s) for s in ("_code", "_id", "_key", "_rank", "_flag", "_number", "_no")):
        return False
    if c in ("month", "year", "day", "no", "week_number_yearly", "week_number_monthly",
             "facility_code"):
        return False
    return True


def is_grain_date_col(name):
    """日次連続性チェックの対象とする「レコード日付」列か（期間境界は除外）。"""
    c = name.lower()
    return not any(w in c for w in ("start", "end", "period"))


def make_runner(client):
    """SELECT/WITH 以外を拒否する読み取り専用クエリ実行関数を返す。"""
    def run(sql):
        head = sql.lstrip().lstrip("(").lstrip().lower()
        if not (head.startswith("select") or head.startswith("with")):
            raise RuntimeError(f"読み取り専用違反: SELECT/WITH以外は実行不可\n{sql[:120]}")
        return list(client.query(sql).result())
    return run


def fq(project, dataset, table):
    return f"`{project}.{dataset}.{table}`"


def get_columns(run, project, dataset, table):
    rows = run(f"""
        SELECT column_name, data_type
        FROM `{project}.{dataset}`.INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    return [(r["column_name"], r["data_type"].upper()) for r in rows]


def phase1_meta(run, client, project, dataset, table):
    meta = {}
    try:
        r = run(f"""
            SELECT row_count, size_bytes,
              FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', TIMESTAMP_MILLIS(creation_time),'Asia/Tokyo') created,
              FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', TIMESTAMP_MILLIS(last_modified_time),'Asia/Tokyo') modified,
              CASE type WHEN 1 THEN 'table' WHEN 2 THEN 'view' ELSE CAST(type AS STRING) END typ
            FROM `{project}.{dataset}.__TABLES__` WHERE table_id = '{table}'
        """)[0]
        meta = dict(r)
    except Exception as e:  # noqa: BLE001
        meta["error"] = str(e)[:120]
    # 更新頻度（直近180日のジョブ履歴）
    try:
        r = run(f"""
            SELECT COUNT(*) writes,
              COUNT(DISTINCT DATE(creation_time,'Asia/Tokyo')) active_days,
              FORMAT_TIMESTAMP('%Y-%m-%d', MIN(creation_time),'Asia/Tokyo') first_day,
              FORMAT_TIMESTAMP('%Y-%m-%d', MAX(creation_time),'Asia/Tokyo') last_day
            FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
            WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 180 DAY)
              AND destination_table.dataset_id = '{dataset}'
              AND destination_table.table_id = '{table}'
              AND (job_type='LOAD' OR statement_type LIKE 'CREATE%' OR statement_type IN ('MERGE','INSERT'))
        """)[0]
        meta["freq"] = dict(r)
    except Exception:  # noqa: BLE001
        meta["freq"] = None
    return meta


def phase2_columns(run, t, cols):
    """カラムごとの NULL率/一意率/カーディナリティ/型別統計/区分値。"""
    # 共通: 総数・NULL・distinct・(文字列の)空文字
    sel = ["COUNT(*) AS _total"]
    for name, typ in cols:
        sel.append(f"COUNTIF(`{name}` IS NULL) AS `n_{name}`")
        sel.append(f"COUNT(DISTINCT `{name}`) AS `d_{name}`")
        if typ == "STRING":
            sel.append(f"COUNTIF(TRIM(`{name}`)='') AS `e_{name}`")
    base = run(f"SELECT {', '.join(sel)} FROM {t}")[0]
    total = base["_total"]

    # 数値統計
    num_cols = [c for c, ty in cols if ty in NUMERIC_TYPES]
    numstats = {}
    if num_cols and total:
        sel = []
        for c in num_cols:
            sel += [
                f"MIN(`{c}`) AS `mn_{c}`", f"MAX(`{c}`) AS `mx_{c}`",
                f"AVG(`{c}`) AS `av_{c}`", f"STDDEV(`{c}`) AS `sd_{c}`",
                f"APPROX_QUANTILES(`{c}`,100) AS `q_{c}`",
            ]
        r = run(f"SELECT {', '.join(sel)} FROM {t}")[0]
        for c in num_cols:
            q = r[f"q_{c}"] or []
            numstats[c] = {
                "min": r[f"mn_{c}"], "max": r[f"mx_{c}"],
                "avg": r[f"av_{c}"], "std": r[f"sd_{c}"],
                "p25": q[25] if len(q) > 25 else None,
                "median": q[50] if len(q) > 50 else None,
                "p75": q[75] if len(q) > 75 else None,
                "p95": q[95] if len(q) > 95 else None,
            }

    # 日付範囲
    date_cols = [c for c, ty in cols if ty in DATE_TYPES]
    datestats = {}
    if date_cols and total:
        sel = []
        for c in date_cols:
            sel += [f"CAST(MIN(`{c}`) AS STRING) AS `lo_{c}`",
                    f"CAST(MAX(`{c}`) AS STRING) AS `hi_{c}`"]
        r = run(f"SELECT {', '.join(sel)} FROM {t}")[0]
        for c in date_cols:
            datestats[c] = {"min": r[f"lo_{c}"], "max": r[f"hi_{c}"]}

    # 区分値（低カーディナリティ列の値とトップ件数）
    cols_out = {}
    low_card = []
    for name, typ in cols:
        nulls = base[f"n_{name}"]
        dist = base[f"d_{name}"]
        nonnull = total - nulls
        info = {
            "type": typ, "nulls": nulls, "dist": dist, "total": total,
            "null_pct": (nulls / total * 100) if total else 0,
            "unique_pct": (dist / nonnull * 100) if nonnull else 0,
            "empty": base.get(f"e_{name}", None),
            "num": numstats.get(name),
            "date": datestats.get(name),
            "values": None,
        }
        cols_out[name] = info
        if 1 < dist <= 20 and typ in ("STRING", "INT64", "INTEGER", "BOOL", "BOOLEAN"):
            low_card.append(name)

    if low_card and total:
        sel = [f"APPROX_TOP_COUNT(`{c}`, 20) AS `v_{c}`" for c in low_card]
        r = run(f"SELECT {', '.join(sel)} FROM {t}")[0]
        for c in low_card:
            cols_out[c]["values"] = [(str(x["value"]), x["count"]) for x in (r[f"v_{c}"] or [])]
    return total, cols_out, low_card


def phase3_segments(run, t, total, cols_out, low_card, axes_limit=4):
    """低カーディナリティ列を軸に、件数・割合と他列NULL率の差を比較。"""
    axes = [c for c in low_card if 2 <= cols_out[c]["dist"] <= 12][:axes_limit]
    other_cols = [c for c in cols_out]
    results = []
    for axis in axes:
        # セグメント件数 + 各列のNULL率
        sel = [f"CAST(`{axis}` AS STRING) AS seg", "COUNT(*) AS cnt"]
        targets = [c for c in other_cols if c != axis]
        for c in targets:
            sel.append(f"ROUND(COUNTIF(`{c}` IS NULL)/COUNT(*)*100,1) AS `np_{c}`")
        rows = run(f"SELECT {', '.join(sel)} FROM {t} GROUP BY seg ORDER BY cnt DESC")
        segs = [{"seg": (r["seg"] if r["seg"] is not None else "(NULL)"),
                 "cnt": r["cnt"], "pct": r["cnt"] / total * 100} for r in rows]
        # NULL率差が20pt超の列を抽出
        flagged = []
        for c in targets:
            vals = [r[f"np_{c}"] for r in rows if r[f"np_{c}"] is not None]
            if vals and (max(vals) - min(vals)) >= 20:
                flagged.append((c, min(vals), max(vals)))
        results.append({"axis": axis, "segs": segs, "flagged": flagged})
    return results


def phase4_quality(run, t, total, cols, cols_out):
    q = {}
    str_cols = [c for c, ty in cols if ty == "STRING"]
    num_cols = [c for c, ty in cols if ty in NUMERIC_TYPES]
    date_cols = [c for c, ty in cols if ty in DATE_TYPES]

    # 完全重複行
    try:
        r = run(f"SELECT COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) AS dup FROM {t} AS t")[0]
        q["dup_rows"] = r["dup"]
    except Exception:  # noqa: BLE001
        q["dup_rows"] = None

    # エラー値・センチネル（文字列列）
    q["sentinels"] = {}
    if str_cols and total:
        lst = ",".join("'" + s.replace("'", "''") + "'" for s in SENTINELS)
        sel = [f"COUNTIF(UPPER(TRIM(`{c}`)) IN ({lst.upper()})) AS `s_{c}`" for c in str_cols]
        r = run(f"SELECT {', '.join(sel)} FROM {t}")[0]
        for c in str_cols:
            if r[f"s_{c}"]:
                q["sentinels"][c] = r[f"s_{c}"]

    # 数値: 外れ値(IQR) と 負値
    q["outliers"] = {}
    q["negatives"] = {}
    if num_cols and total:
        sel = []
        bounds = {}
        for c in num_cols:
            st = cols_out[c]["num"] or {}
            p25, p75 = st.get("p25"), st.get("p75")
            # 量的指標のみ外れ値判定（ID/コード/区分/ほぼ一意は除外）
            measure = is_measure_col(c) and cols_out[c]["unique_pct"] < 90
            if p25 is not None and p75 is not None and measure:
                iqr = p75 - p25
                lo, hi = p25 - 1.5 * iqr, p75 + 1.5 * iqr
                bounds[c] = (lo, hi)
                sel.append(f"COUNTIF(`{c}` < {lo} OR `{c}` > {hi}) AS `o_{c}`")
            sel.append(f"COUNTIF(`{c}` < 0) AS `g_{c}`")
        if sel:
            r = run(f"SELECT {', '.join(sel)} FROM {t}")[0]
            for c in num_cols:
                # 希少(全体の2%未満)な外れ値のみ＝真の異常値として報告（分布の歪みは除外）
                if c in bounds and r.get(f"o_{c}"):
                    if total and r[f"o_{c}"] / total < 0.02:
                        q["outliers"][c] = r[f"o_{c}"]
                if r.get(f"g_{c}"):
                    q["negatives"][c] = r[f"g_{c}"]

    # 日付: 連続性（欠損日）と start>end 逆転
    q["date_gaps"] = {}
    for c in date_cols:
        if not is_grain_date_col(c):
            continue  # 期間境界列(start/end/period)は連続性チェック対象外
        d = cols_out[c]["date"]
        if d and d["min"] and d["max"]:
            try:
                r = run(f"""SELECT DATE_DIFF(DATE(MAX(`{c}`)), DATE(MIN(`{c}`)), DAY)+1 AS span,
                            COUNT(DISTINCT DATE(`{c}`)) AS days FROM {t} WHERE `{c}` IS NOT NULL""")[0]
                gap = (r["span"] or 0) - (r["days"] or 0)
                if gap > 0:
                    q["date_gaps"][c] = {"span": r["span"], "days": r["days"], "missing": gap}
            except Exception:  # noqa: BLE001
                pass
    names = {c for c, _ in cols}
    if "start_date" in names and "end_date" in names:
        try:
            r = run(f"SELECT COUNTIF(end_date < start_date) AS rev FROM {t}")[0]
            if r["rev"]:
                q["date_reversed"] = r["rev"]
        except Exception:  # noqa: BLE001
            pass
    return q


def num(x):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:,.2f}".rstrip("0").rstrip(".")
    return f"{x:,}" if isinstance(x, int) else str(x)


def render(dataset, table, meta, total, cols_out, segments, quality):
    L = [f"## {dataset}.{table}", ""]
    # Phase1
    typ = meta.get("typ", "?")
    size = meta.get("size_bytes")
    L.append(f"- 種別: **{typ}** / 行数: **{num(total)}**"
             + (f" / サイズ: {size/1e6:.1f}MB" if size else ""))
    L.append(f"- 作成: {meta.get('created','?')} / 最終更新: {meta.get('modified','?')}")
    f = meta.get("freq")
    if f and f.get("writes"):
        L.append(f"- 更新頻度(直近180日): 書込{f['writes']}回 / 稼働{f['active_days']}日 "
                 f"({f['first_day']}〜{f['last_day']})")
    L.append("")

    # Phase2
    L.append("### Phase2 カラム基本統計")
    L.append("| カラム | 型 | NULL率 | 一意率 | distinct | 数値/日付の範囲 | 区分値(上位) |")
    L.append("|---|---|--:|--:|--:|---|---|")
    for c, i in cols_out.items():
        rng = ""
        if i["num"]:
            n = i["num"]
            rng = f"min {num(n['min'])} / median {num(n['median'])} / max {num(n['max'])} / σ {num(n['std'])}"
        elif i["date"]:
            rng = f"{i['date']['min']} 〜 {i['date']['max']}"
        vals = ""
        if i["values"]:
            vals = ", ".join(f"{v}({num(cnt)})" for v, cnt in i["values"][:6])
            if len(i["values"]) > 6:
                vals += " …"
        flag = " ⚠️全NULL" if i["null_pct"] == 100 else ""
        L.append(f"| {c} | {i['type']} | {i['null_pct']:.0f}% | {i['unique_pct']:.0f}% | "
                 f"{num(i['dist'])} | {rng} | {vals}{flag} |")
    L.append("")

    # Phase3
    if segments:
        L.append("### Phase3 セグメント別")
        for s in segments:
            top = " / ".join(f"{x['seg']}: {num(x['cnt'])}({x['pct']:.0f}%)" for x in s["segs"][:8])
            L.append(f"- 軸 **{s['axis']}**: {top}")
            if s["flagged"]:
                for c, lo, hi in s["flagged"]:
                    L.append(f"  - ⚠️ `{c}` のNULL率がセグメント間で差大（{lo:.0f}%〜{hi:.0f}%）")
        L.append("")

    # Phase4
    L.append("### Phase4 品質チェック")
    findings = []
    if quality.get("dup_rows"):
        findings.append(f"完全重複行: **{num(quality['dup_rows'])}件**")
    if quality.get("sentinels"):
        s = ", ".join(f"`{c}`={num(n)}" for c, n in quality["sentinels"].items())
        findings.append(f"エラー値/センチネル混入: {s}")
    if quality.get("outliers"):
        s = ", ".join(f"`{c}`={num(n)}" for c, n in quality["outliers"].items())
        findings.append(f"外れ値(IQR±1.5): {s}")
    if quality.get("negatives"):
        s = ", ".join(f"`{c}`={num(n)}" for c, n in quality["negatives"].items())
        findings.append(f"負値: {s}")
    if quality.get("date_gaps"):
        s = ", ".join(f"`{c}` 欠損{num(v['missing'])}日({v['days']}/{v['span']})"
                      for c, v in quality["date_gaps"].items())
        findings.append(f"日付の欠損日: {s}")
    if quality.get("date_reversed"):
        findings.append(f"開始日>終了日の逆転: **{num(quality['date_reversed'])}件**")
    full_null = [c for c, i in cols_out.items() if i["null_pct"] == 100]
    if full_null:
        findings.append(f"全行NULL(未投入)列: {', '.join(full_null)}")
    if findings:
        for x in findings:
            L.append(f"- {x}")
    else:
        L.append("- 目立った問題は検出されず。")
    L.append("")
    return "\n".join(L)


def profile(project, dataset, table):
    client = bigquery.Client(project=project)
    run = make_runner(client)
    t = fq(project, dataset, table)
    cols = get_columns(run, project, dataset, table)
    meta = phase1_meta(run, client, project, dataset, table)
    total, cols_out, low_card = phase2_columns(run, t, cols)
    segments = phase3_segments(run, t, total, cols_out, low_card) if total else []
    quality = phase4_quality(run, t, total, cols, cols_out) if total else {}
    md = render(dataset, table, meta, total, cols_out, segments, quality)
    # サマリー用の主要所見
    findings = []
    full_null = [c for c, i in cols_out.items() if i["null_pct"] == 100]
    if full_null:
        findings.append(f"全NULL列 {len(full_null)}個")
    if quality.get("dup_rows"):
        findings.append(f"重複{num(quality['dup_rows'])}行")
    if quality.get("sentinels"):
        findings.append(f"エラー値 {len(quality['sentinels'])}列")
    if quality.get("date_reversed"):
        findings.append("日付逆転あり")
    if quality.get("date_gaps"):
        findings.append(f"日付欠損 {len(quality['date_gaps'])}列")
    return {"md": md, "dataset": dataset, "table": table, "rows": total,
            "modified": meta.get("modified"), "type": meta.get("typ"),
            "findings": findings, "cols": {c: (i["type"], i["unique_pct"], i["null_pct"])
                                           for c, i in cols_out.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="digital-well-456700-i9")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--table", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    md = profile(args.project, args.dataset, args.table)["md"]
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"出力: {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
