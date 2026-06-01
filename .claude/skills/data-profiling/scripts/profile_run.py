"""複数テーブルを並列にプロファイルし、テーブル間整合チェックを加えて report.md を生成する。

- テーブル探索 → スレッドプールで並列プロファイル（各テーブルは profile_table.profile を呼ぶ）
- テーブル間：共有キー列の参照整合（孤児レコード）を読み取りで検証
- 出力：data-profile-output/report.md（＋任意で per-table 中間md）

【厳守】BigQueryは読み取り(SELECT)のみ。書き込み・変更・削除は一切行わない。

使い方:
  python profile_run.py --datasets docomo_event_raw docomo_event_intermediate ... [--workers 8]
"""

import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.cloud import bigquery

import profile_table as pt

DEFAULT_DATASETS = [
    "docomo_event_raw",
    "docomo_event_intermediate",
    "docomo_event_mart",
]

# テーブル間整合で参照整合を見る「キーらしい」列の判定
def is_keyish(col):
    c = col.lower()
    return c.endswith("_code") or c.endswith("_id") or c in ("facility_code", "date", "facility_name")


def list_tables(client, project, dataset):
    sql = (f"SELECT table_name, table_type FROM `{project}.{dataset}`.INFORMATION_SCHEMA.TABLES "
           f"ORDER BY table_name")
    return [(r["table_name"], r["table_type"]) for r in client.query(sql).result()]


def cross_table_checks(project, results):
    """共有キー列について、親(一意)→子の参照整合(孤児)を検証する。"""
    client = bigquery.Client(project=project)
    run = pt.make_runner(client)
    # 列名 -> [(dataset, table, unique_pct, null_pct)]
    index = {}
    for r in results:
        for col, (typ, upct, npct) in r["cols"].items():
            if is_keyish(col):
                index.setdefault(col, []).append((r["dataset"], r["table"], upct, npct))

    lines = []
    for col, holders in sorted(index.items()):
        if len(holders) < 2:
            continue
        parents = [(ds, tb) for ds, tb, up, np_ in holders if up >= 99.5 and np_ == 0]
        if len(parents) > 1:
            # 親候補が複数なら master を名に含むものを優先
            masters = [p for p in parents if "master" in p[1].lower()]
            parents = masters
        if len(parents) != 1:
            continue  # 親が一意に定まらない場合はスキップ
        pds, ptb = parents[0]
        for ds, tb, up, np_ in holders:
            if (ds, tb) == (pds, ptb):
                continue
            try:
                orphan = run(f"""
                    SELECT COUNT(*) AS n FROM `{project}.{ds}.{tb}` c
                    WHERE c.`{col}` IS NOT NULL AND NOT EXISTS (
                      SELECT 1 FROM `{project}.{pds}.{ptb}` p WHERE p.`{col}` = c.`{col}`)
                """)[0]["n"]
                mark = "✅整合" if orphan == 0 else f"⚠️孤児 {orphan:,}件"
                lines.append(f"- `{ds}.{tb}.{col}` → `{pds}.{ptb}.{col}` : {mark}")
            except Exception as e:  # noqa: BLE001
                lines.append(f"- `{ds}.{tb}.{col}` → `{pds}.{ptb}.{col}` : 検証失敗 ({str(e)[:60]})")
    return lines


def build_report(results, cross_lines, scope):
    L = ["# データプロファイリング レポート", ""]
    L.append(f"対象: {scope}")
    L.append("※ BigQueryは読み取り(SELECT)のみで調査（書き込みなし）。")
    L.append("")
    # サマリー
    L.append("## サマリー")
    L.append("| テーブル | 種別 | 行数 | 最終更新 | 主な所見 |")
    L.append("|---|---|--:|---|---|")
    for r in sorted(results, key=lambda x: (x["dataset"], x["table"])):
        f = " / ".join(r["findings"]) if r["findings"] else "—"
        rows = f"{r['rows']:,}" if isinstance(r["rows"], int) else "?"
        L.append(f"| {r['dataset']}.{r['table']} | {r.get('type','?')} | {rows} | "
                 f"{r.get('modified','?')} | {f} |")
    L.append("")
    # テーブル間整合
    L.append("## テーブル間の参照整合（共有キー）")
    L.extend(cross_lines if cross_lines else ["- 対象となる共有キーは検出されず。"])
    L.append("")
    # 各テーブル詳細
    L.append("## テーブル別 詳細")
    L.append("")
    for r in sorted(results, key=lambda x: (x["dataset"], x["table"])):
        L.append(r["md"])
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="digital-well-456700-i9")
    ap.add_argument("--datasets", nargs="*", default=DEFAULT_DATASETS)
    ap.add_argument("--tables", nargs="*", default=None,
                    help="dataset.table 形式で対象を明示（省略時はdatasets内の全テーブル）")
    ap.add_argument("--out", default="docs/データプロファイリングレポート.md")
    ap.add_argument("--intermediate-dir", default=None,
                    help="指定すると per-table の中間mdも出力")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    client = bigquery.Client(project=args.project)

    # 対象テーブルの決定
    targets = []
    if args.tables:
        for spec in args.tables:
            ds, tb = spec.split(".", 1)
            targets.append((ds, tb))
    else:
        for ds in args.datasets:
            for tb, _typ in list_tables(client, args.project, ds):
                targets.append((ds, tb))

    print(f"対象 {len(targets)} テーブルを並列プロファイル（workers={args.workers}）…")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(pt.profile, args.project, ds, tb): (ds, tb) for ds, tb in targets}
        for fut in as_completed(futs):
            ds, tb = futs[fut]
            try:
                res = fut.result()
                results.append(res)
                if args.intermediate_dir:
                    os.makedirs(args.intermediate_dir, exist_ok=True)
                    with open(os.path.join(args.intermediate_dir, f"{ds}.{tb}.md"),
                              "w", encoding="utf-8") as f:
                        f.write(res["md"])
                print(f"  ✓ {ds}.{tb}")
            except Exception as e:  # noqa: BLE001
                print(f"  ✗ {ds}.{tb}: {str(e)[:100]}")

    print("テーブル間整合チェック…")
    cross = cross_table_checks(args.project, results)

    scope = ", ".join(args.datasets) if not args.tables else f"{len(targets)}テーブル"
    report = build_report(results, cross, scope)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"レポート生成: {args.out}（{len(results)}テーブル）")


if __name__ == "__main__":
    main()
