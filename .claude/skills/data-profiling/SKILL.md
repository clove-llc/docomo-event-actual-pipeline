---
name: data-profiling
description: BigQueryのテーブル群を読み取り(SELECT)のみで並列にプロファイルし、データ品質・特性のMarkdownレポートを生成する。「テーブルのデータを調査して」「データプロファイリングして」「データ品質を調べて」「テーブルの特性を分析して」等のときに使う。【厳守】BigQueryへの書き込み・変更・削除は一切しない。許可されるのは参照(SELECT)のみ。
---

# データプロファイリング（BigQuery・読み取り専用）

テーブルのメタ情報・統計・分布・品質を、4フェーズで**現状の事実として**調査し、Markdownレポートにまとめる。

> ## 【最重要】絶対遵守の制約
>
> **BigQueryのテーブルへの書き込み・作成・変更・削除を一切行わない。許可されるのは参照（SELECT）のみ。**
> - INSERT / UPDATE / MERGE / DELETE / CREATE / DROP / TRUNCATE / LOAD / `bq load` 等は禁止。
> - スクリプトの `make_runner()` が **SELECT / WITH 以外のクエリを実行時に拒否**する（二重の安全装置）。
> - 業務プロセスの推測・憶測はしない。**観測された事実のみ**を報告する。

## 前提
- poetry 環境（`google-cloud-bigquery` 必要）、ADC認証済み（`gcloud auth application-default login`）。
- スクリプト:
  - `.claude/skills/data-profiling/scripts/profile_table.py` … 1テーブルをプロファイル（md出力）
  - `.claude/skills/data-profiling/scripts/profile_run.py` … 複数テーブルを**並列**実行＋テーブル間整合＋レポート集約

## 使い方

### 複数テーブルを並列プロファイル（推奨）
```bash
poetry run python .claude/skills/data-profiling/scripts/profile_run.py \
  --datasets docomo_event_raw docomo_event_intermediate docomo_event_mart \
  --workers 10
```
- `--datasets` 対象データセット（省略時は raw/intermediate/mart）
- `--tables docomo_event_raw.raw_facility_master ...` 対象を明示指定（省略時はdataset内全テーブル）
- `--workers` 並列数（ThreadPoolExecutorでSELECTを同時実行）
- `--out` レポート出力先（既定 `docs/データプロファイリングレポート.md`）
- `--intermediate-dir` 指定するとテーブル別の中間mdも出力
- `--project` GCPプロジェクト（既定 `digital-well-456700-i9`）

### 1テーブルだけ
```bash
poetry run python .claude/skills/data-profiling/scripts/profile_table.py \
  --dataset docomo_event_raw --table raw_facility_master
```

## 調査フェーズ（各テーブル）
- **Phase1 情報収集**: 行数 / サイズ / 種別(table/view) / 作成・最終更新時刻 / 更新頻度（直近180日のジョブ履歴）/ カラム一覧・型。
- **Phase2 基本統計**（カラム単位）: NULL率 / 一意率 / カーディナリティ / 数値統計(min/max/avg/median/σ/p25/p75/p95) / 日付範囲 / 低カーディナリティ列の区分値・出現頻度。
- **Phase3 セグメント別**: 値2〜12の低カーディナリティ列を軸に、件数・割合と、他列のNULL率がセグメント間で20pt以上差がある箇所を抽出。
- **Phase4 品質チェック**: 完全重複行 / エラー値・センチネル(`#N/A`等) / 外れ値(IQR±1.5、ID列は除外) / 負値 / 日付の欠損日・開始終了の逆転 / 全行NULL列。

## テーブル間（クロス）チェック
- 共有する「キーらしい列」(`*_code` / `*_id` / `facility_code` / `date` / `facility_name`)について、
  **親(一意・非NULL、名に`master`を優先)→子の参照整合（孤児レコード）**を検証。
- 孤児があれば件数を表示（表記ゆれや未マッピングの検出に有効）。

## 出力
`docs/データプロファイリングレポート.md`:
1. サマリー表（テーブル / 種別 / 行数 / 最終更新 / 主な所見）
2. テーブル間の参照整合（共有キー）
3. テーブル別 詳細（Phase1〜4）

## 並列化
`profile_run.py` は ThreadPoolExecutor で各テーブルのプロファイルを同時実行（各スレッドが独自のBigQueryクライアントでSELECTを発行）。テーブル数が多い場合に有効。

## 注意
- 大規模テーブルでも集計は `APPROX_QUANTILES` / `APPROX_TOP_COUNT` を用い負荷を抑える。
- レポートは生成時点のスナップショット。レポートは既存があれば上書きする。
- このスキルは**現状調査のみ**。原因の推測や修正提案が必要な場合は、レポートの事実をもとに別途検討する。
