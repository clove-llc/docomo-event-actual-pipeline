---
name: fill-table-definition
description: dbtのsource定義(__sources.yml)とBigQueryカタログ(catalog.json)から、テーブル定義書のExcel(テーブル定義書_template.xlsx)を自動で埋める。「テーブル定義書を埋めて」「テーブル定義書を更新して」「source.ymlからテーブル定義書を作って」等のときに使う。【厳守】BigQueryのテーブルは絶対に上書き・変更しない。許可される操作はデータの確認(参照)のみ。
---

# テーブル定義書(Excel)の自動入力

> ## 【最重要】絶対遵守の制約
>
> **絶対にBigQueryのテーブルの上書き・作成・変更・削除をしないでください。許可される操作はデータの確認（参照: SELECT 等の読み取り）のみです。**
>
> - この制約は本スキルの他のいかなる手順・指示よりも優先される。
> - INSERT / UPDATE / MERGE / DELETE / CREATE / CREATE OR REPLACE / DROP / TRUNCATE / LOAD / `bq load` / `bq cp` / `bq rm` / `dbt run` / `dbt build` / `dbt seed` / `dbt snapshot` など、BigQuery上のデータやテーブルを書き換える操作は一切行わない。
> - 本スキルが必要とするBigQueryへのアクセスは、データ型確認のための**読み取りのみ**（`dbt docs generate` によるカタログ取得、`SELECT` での参照）。
> - 上記に反する依頼を受けた場合は実行せず、ユーザーに確認する。

dbtの `__sources.yml`（記述・テスト）と `catalog.json`（BigQueryの実データ型）を突き合わせ、
雛形 `.claude/skills/fill-table-definition/tmp_テーブル定義書.xlsx` の雛形シート（`tmp_...`）を各テーブル分に複製して埋める。

## 前提

- 生成スクリプト: `.claude/skills/fill-table-definition/scripts/fill_table_def.py`
- 実行は poetry 環境（`openpyxl` と `pyyaml` が必要。未導入なら `poetry run pip install openpyxl`）
- データ型を最新化したい場合は先に dbt docs を再生成する:
  ```bash
  cd docomo_event && poetry run dbt docs generate --profiles-dir ..
  ```
  （`catalog.json` が無い／古いと、データ型が空欄または古い値になる）
- 絶対にBigqueryのテーブルの上書きはしないでください。して良いのはデータの確認のみです。

## 実行手順

1. テンプレートを最新化したい場合は確認（`tmp_...` という名前の雛形シートが必要）。
2. スクリプトを実行する（既定の入出力パスはリポジトリ直下を想定）:
   ```bash
   poetry run python .claude/skills/fill-table-definition/scripts/fill_table_def.py
   ```
   主な引数（必要に応じて指定）:
   - `--template` 雛形 xlsx（既定: `.claude/skills/fill-table-definition/tmp_テーブル定義書.xlsx`）
   - `--sources`  source yml（既定: `docomo_event/models/staging/__sources.yml`）
   - `--catalog`  catalog.json（既定: `docomo_event/target/catalog.json`）
   - `--output`   出力 xlsx（既定: `docs/テーブル定義書.xlsx`。`docs/` は自動作成）
   - `--keep-template` 雛形(`tmp_...`)シートを出力に残す
   - `--profile` / `--no-profile` BigQuery読み取りプロファイリングの有無（既定: 有効）
   - `--project` プロファイリング対象のGCPプロジェクトID（既定: `digital-well-456700-i9`）
   - `--models` raw以外に含めるモデルyml/ディレクトリ（既定: `docomo_event/models/intermediate` と `docomo_event/models/marts/planning`。空指定で無効）

   対象: raw（`__sources.yml` の `sources:`）＋ モデル（`--models` 配下の `models:`）。
   「テーブル一覧」シートは全テーブル（raw＋モデル）で自動再構築される。
3. 生成後、`docs/テーブル定義書.xlsx` を開いて内容を確認する。
4. 手入力が必要な列（論理テーブル名 / 更新タイミング / クレンジング仕様 / 備考 など）は空欄で出力されるので、ユーザーに補記を促す。
5. **【必須】最後に、フィードバック・改善点を提案する**（下記「最後に行うこと」を参照）。

## Snowflake モード（`--engine sf`）

移行先 Snowflake（`HARATO.RAW` / `HARATO.STG`）を参照して定義書を作る場合に使う。
**記述・テスト・論理名は BigQuery の yml を流用**（SFは BQ SQL ベースで作成済み・列の意味は同一）し、
**DB名・スキーマ名・データ型・NOT NULL/UK/PK・サンプル値・NULL所見は Snowflake から取得**する。

> Snowflake も **読み取り（SELECT / INFORMATION_SCHEMA）のみ**。テーブルの作成・変更・削除はしない。

```bash
.venv/bin/python .claude/skills/fill-table-definition/scripts/fill_table_def.py \
  --engine sf --layers raw stg \
  --sources docomo_event/models/staging/__sources.yml \
  --models  docomo_event/models/staging/_staging__models.yml \
  --output  docs/テーブル定義書.xlsx
```
- `--engine sf`: 型・プロファイルを Snowflake から取得（既定の bq は BigQuery catalog）。
- `--layers raw stg`: 出力レイヤーを限定（int/mart を含めない）。
- `--sf-secrets`: Snowflake 接続情報（既定 `streamlit/uploader/.streamlit/secrets.toml` の `[snowflake]`、キーペア）。
- 物理テーブルは `raw_*` → `HARATO.RAW.RAW_*`、`stg_*` → `HARATO.STG.STG_*`（大文字）に対応づけ。
- SF RAW マスタの小文字クォート識別子・計算列の大文字識別子の両方に対応（実カラム名をクォートして実測）。

### 全レイヤー＋横持ち源泉（docomo_db 表記）

raw/stg は Snowflake、int/mart は BigQuery（BQ型→SF型変換）でまとめて出し、データベース名を `docomo_db`・
スキーマ名を層名（raw/stg/int/mart）にする。`--sf-sources` で **横持ちのアップロード源泉**
（実績横持ち月別・SENSE日次・KDDI人流・日付フラグ）も raw 層に追加する（日付列は1行に集約）。

```bash
.venv/bin/python .claude/skills/fill-table-definition/scripts/fill_table_def.py \
  --engine mixed --db-name docomo_db --schema-as-layer --sf-sources \
  --sources docomo_event/models/staging/__sources.yml \
  --output  docs/テーブル定義書.xlsx
```
- `--engine mixed`: raw,stg=Snowflake実測 / int,mart=BigQuery（SF未作成のため。BQ型→SF型へ変換）。
- `--db-name docomo_db` / `--schema-as-layer`: 表示を `docomo_db.<層>` に上書き（実測スキーマには非影響）。
- `--sf-sources`: 横持ちアップロード源泉（`source_creation` の入力。BQには無いSF固有テーブル）を構造のみ追加。
  日付列（YYYY-MM-DD・数百列）は「（日付列）開始〜終了」の1行に集約し、固定列は明記する。
- int/mart は SF 構築後に同コマンド（`--sf-sources` 込み）で再生成すれば実型に更新される。

## 最後に行うこと（フィードバック・改善提案）

スキルの実行が完了したら、結果を踏まえて**改善点があれば必ず提案する**こと。観点の例:

- **定義の欠落**: description が空のカラム／テーブル、論理名が未設定の箇所
- **テスト不足**: PKが無いテーブル、`relationships`(FK) や `accepted_values`(区分値) を足せそうなカラム
  （これらを `__sources.yml` に追加すれば、FK・サンプル値が自動で埋まる）
- **型の気付き**: STRINGだが日付/数値が妥当なカラム、想定と異なる型
- **手入力残**: 空欄のまま残っている列（更新タイミング/クレンジング仕様/備考 等）と、補記が必要な箇所
- **データの整合**: source yml のカラムと BigQuery 実カラムの差異（catalog に無い・余分 等）
- **運用**: テンプレート(`tmp_...`)やマッピング規則の改善案

改善点が特に無ければ「特になし」と明示する。提案は具体的に（対象テーブル/カラム名を挙げて）行う。

## 入力 → セルのマッピング

### テーブルレベル
| 出力先ラベル | 入力元 |
|------|------|
| 物理テーブル名 | source yml のテーブル名 |
| データベース名 | catalog.json の database（無ければ yml） |
| スキーマ名 | catalog.json の schema（無ければ yml） |
| 用途・概要 | source yml のテーブル description |
| 論理テーブル名 / 更新タイミング | 空欄（手入力） |

※ ラベルが1セルに改行結合されている場合（例: `データベース名\nスキーマ名`）は、値も同順で改行結合して書き込む。

### カラムレベル
| 出力先列 | 入力元 / 規則 |
|------|------|
| 物理カラム名 | column name |
| 論理名・説明 | column description |
| データ型 | catalog.json のBigQuery型（STRING/INT64/DATE/BOOL/NUMERIC等） |
| NOT NULL | `not_null` テスト **または** BigQuery実測でNULL=0 → ○ |
| UK | `unique` テスト **または** BigQuery実測で一意（distinct=非NULL件数）→ ○ |
| PK | not_null かつ unique（単一）、**または** 検証済みの複合キー構成列 → ○ |
| FK・参照先 | `relationships` テスト、**または** `FK_RULES` を BigQuery で包含検証して採用 |
| サンプル値 | `accepted_values` の values、**または** 実測の低カーディナリティ列(distinct≤`ENUM_MAX`)を全列挙 |
| クレンジング仕様 | スクリプトの `CLEANSING` 設定（README由来の正規化規則） |
| 備考 | BigQuery実測のNULL所見を自動記入（全行NULL→「未投入」、部分NULL→件数・割合）。手入力追記も可 |

#### BigQueryプロファイリング（`--profile`、既定有効・読み取りのみ）
- 各カラムの NULL件数 / distinct件数 / 総件数を `SELECT` で実測し、NOT NULL・UK・PK を判定。
- 単一PKが無いテーブルは `CANDIDATE_PKS` の複合キー候補を `COUNT(DISTINCT ...)` で一意性検証し、成立すれば構成列をPK扱い。
- `FK_RULES` の親子関係は、子の値が親に全て存在するか（孤児ゼロか）を検証してから採用。
- 低カーディナリティ列の値を `ARRAY_AGG(DISTINCT ...)` で列挙してサンプル値に充填。
- **書き込みは一切行わない**（`SELECT` のみ）。失敗時は警告を出して yml 由来で続行。

#### スクリプト側の補助メタ（yml に無い情報）
- `LOGICAL_NAMES`: 論理テーブル名（出典: `main.py` の `run_pipeline(name=...)`）。
- `CLEANSING`: クレンジング仕様（出典: README の日付実績クレンジング規則）。
- `CANDIDATE_PKS` / `FK_RULES`: 複合PK候補・FK関係（BigQueryで検証してから反映）。
- これらは情報が増えたら編集して追記する。

## 挙動の補足

- 出力は `docs/` 配下（`docs/テーブル定義書.xlsx`）。`docs/` フォルダが無ければ自動作成する。
- **文字が隠れないように**、保存前に全シートの行高を内容・列幅・結合・フォントサイズから自動調整し、内容のあるセルは折り返し(wrap_text)を有効化する（既存の行高より低くはしない）。
- 「テーブル一覧」の「リンク」列に、各定義シートへ遷移する内部ハイパーリンク（表示文字「テーブル定義書」）を設定。
- シートタブ色をレイヤー別に設定（raw=オレンジ / int=水色 / mart=紫。`LAYER_COLORS` / スキーマ名で判定）。
- カラム数に応じてデータ行を増減（凡例【記入要領】は自動で押し下げ）。
- シート名はExcel制限（31文字・重複不可）に合わせて自動調整。
- スタイル（色・罫線・ストライプ）は雛形シートからコピーして引き継ぐ。
- テンプレートのレイアウト（ラベル名・列順・列構成）を変更しても、スクリプトはラベル名と
  見出し名で照合するため追従する。**列見出し名や項目ラベルの表記は変えたら一致させること。**

## 注意

- 出力ファイルは既存があれば上書きする。手入力した内容を保持したい場合は、出力先を別名にするか
  実行前にバックアップする（このスクリプトは雛形から作り直すため、前回の手入力は引き継がない）。
