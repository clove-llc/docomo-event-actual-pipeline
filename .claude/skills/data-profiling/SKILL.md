---
name: data-profiling
description: BigQueryのテーブル群を読み取り(SELECT)のみで並列にプロファイルし、データ品質・特性のMarkdownレポートを生成する。「テーブルのデータを調査して」「データプロファイリングして」「データ品質を調べて」「テーブルの特性を分析して」等のときに使う。【厳守】BigQueryへの書き込み・変更・削除は一切しない。許可されるのは参照(SELECT)のみ。
---

# データプロファイリング（BigQuery・読み取り専用）

テーブルのメタ情報・統計・分布・品質を、4フェーズで**現状の事実として**調査し、
**テーブル単位のExcelレポート**（表紙 / テーブル一覧 / テーブル別シート）にまとめる。

> ## 【最重要】絶対遵守の制約
>
> **BigQueryのテーブルへの書き込み・作成・変更・削除を一切行わない。許可されるのは参照（SELECT）のみ。**
> - INSERT / UPDATE / MERGE / DELETE / CREATE / DROP / TRUNCATE / LOAD / `bq load` 等は禁止。
> - スクリプトの `make_runner()` が **SELECT / WITH 以外のクエリを実行時に拒否**する（二重の安全装置）。
> - 業務プロセスの推測・憶測はしない。**観測された事実のみ**を報告する。

## 前提
- poetry 環境（`google-cloud-bigquery` 必要）、ADC認証済み（`gcloud auth application-default login`）。
- スクリプト:
  - `.claude/skills/data-profiling/scripts/profile_table.py` … 1テーブルをプロファイル（構造化結果を返す。単体実行時はmd表示）
  - `.claude/skills/data-profiling/scripts/report_xlsx.py` … 結果をテーブル別シートのExcelに描画
  - `.claude/skills/data-profiling/scripts/profile_run.py` … 複数テーブルを**並列**実行＋テーブル間整合＋Excel集約

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
- `--out` レポート出力先（既定 `docs/データプロファイリングレポート.xlsx`）
- `--gen-date` 表紙の生成日（既定: 当日JST）
- `--project` GCPプロジェクト（既定 `digital-well-456700-i9`）

### 1テーブルだけ
```bash
poetry run python .claude/skills/data-profiling/scripts/profile_table.py \
  --dataset docomo_event_raw --table raw_facility_master
```

## 調査フェーズ（各テーブル）
- **Phase1 情報収集**: 行数 / サイズ / 種別(table/view) / 作成・最終更新時刻 / 更新頻度（直近180日のジョブ履歴）/ カラム一覧・型。日付グレイン列(`date`/`event_date`等)があれば**直近7日のレコード数**も概要に表示。
- **Phase2 基本統計**（カラム単位）: NULL率 / 一意率 / カーディナリティ / 数値統計(min・中央・max・σ を列分け、p25/p75/p95も内部利用) / 日付範囲 / 低カーディナリティ列の区分値・出現頻度。
- **Phase3 セグメント別**: 値2〜12の低カーディナリティ列を「軸」に、区分別件数に加え、**NULL率(差≥20pt) / 一意率(差≥50pt) / 数値平均(最大が最小の2倍以上)** が区分間で大きく異なる列を検出。各所見は**区分別の内訳を小表で表示**。差大が多い場合は**スコア順で1シート最大4件**まで。
- **Phase4 品質チェック**: 完全重複行 / エラー値・センチネル(`#N/A`等、**実際に入っていた値の内訳付き**) / 外れ値(IQR±1.5、ID列除外、**例値付き**) / 負値(最小値付き) / 日付の欠損日(**欠損日の例付き**)・開始終了の逆転 / 全行NULL列。
- 各所見には**平易な説明**を付与（用語の意味・何が疑われるか）。注意マークは絵文字を使わず `▲`（注意）/ `○`（整合）で表記（フォント文字化け防止）。

## テーブル間（クロス）チェック
- 共有する「キーらしい列」(`*_code` / `*_id` / `facility_code` / `date` / `facility_name`)について、
  **親(一意・非NULL、名に`master`を優先)→子の参照整合（孤児レコード）**を検証。
- 「孤児」＝子テーブルの値のうち親に存在しない件数。各テーブルシートには**そのテーブルに関係する分のみ**を、説明付きで掲載。

## 出力（Excel・テーブル単位）
`docs/データプロファイリングレポート.xlsx`（体裁は「テーブル定義書」と同様）:
1. **表紙**: 対象データセット / プロジェクト / 生成日 / テーブル数 / 読み取りのみの明記
2. **テーブル一覧**（タブ青）: No / 物理テーブル名 / 論理名 / 行数 / 最終更新 / 主な所見 / **リンク**（各詳細シートへ内部リンク「レポート」）
3. **テーブル別シート**（タブ色＝レイヤー別: raw=オレンジ / int=水色 / mart=紫）
   - A1=物理テーブル名（1行表示）
   - ■ テーブル概要（Phase1）/ ■ Phase2 カラム別プロファイル / ■ Phase3 セグメント別 / ■ Phase4 品質チェック / ■ テーブル間整合（このテーブル関連分）

描画は `report_xlsx.py`。行高は内容に合わせ自動調整（文字が隠れない）。見出し・箇条書きは折り返さず1行。

## 並列化
`profile_run.py` は ThreadPoolExecutor で各テーブルのプロファイルを同時実行（各スレッドが独自のBigQueryクライアントでSELECTを発行）。テーブル数が多い場合に有効。

## 注意
- 大規模テーブルでも集計は `APPROX_QUANTILES` / `APPROX_TOP_COUNT` を用い負荷を抑える。
- レポートは生成時点のスナップショット。既存があれば上書きする。
- このスキルは**現状調査のみ**。原因の推測や修正提案が必要な場合は、レポートの事実をもとに別途検討する。
