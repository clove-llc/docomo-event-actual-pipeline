---
name: numerical-verification
description: BigQuery（移行元）と Snowflake（移行先）のテーブルを行レベルで突合し、dbtレイヤー別（raw/stg/int/mart）に数値検証ドキュメントを生成する。「数値検証して」「BQとSnowflakeを突合して」「移行で値が一致するか確認して」「BQ↔SFの差分を見て」等のときに使う。【厳守】BigQueryへの書き込み・変更・削除は一切しない。許可されるのは参照(SELECT)のみ。
---

# 数値検証（BigQuery ↔ Snowflake）

BQ→Snowflake 移行で、Snowflake 側が移行元 BigQuery と**数値的に一致**するかを
**行レベル（多重集合）**で突合し、**dbtレイヤー別**に検証ドキュメントを残す。

> ## 【最重要】絶対遵守の制約
> **BigQuery への書き込み・作成・変更・削除を一切行わない。許可されるのは参照（SELECT）のみ。**
> Snowflake 側も既存テーブルの **SELECT のみ**（このスキルは検証であり、ロード・変換はしない）。

## 前提
- 認証
  - BigQuery: ADC（`gcloud auth application-default login`）。失効時は `! gcloud auth application-default login` をユーザーに依頼。
  - Snowflake: env_var `SNOWFLAKE_ACCOUNT/USER/PRIVATE_KEY_PATH/ROLE/WAREHOUSE/DATABASE`（dbt プロファイル `dbt_project` と同じ）。
- 依存: `google-cloud-bigquery` / `snowflake-connector-python` / `pandas`（両方入った環境で実行）。
- 比較エンジン: `docomo_event_sf/tools/verify_code.py`（対象表・列型・除外列・正規化を定義）。

## 比較・正規化の方針（verify_code.py に実装）
- **多重集合**で突合（重複行があるため set ではなく Counter）。
- DB間の値表現差は **Python（verify_code.py）側で巻き取る**:
  - num→float（小数9桁丸めで IEEE ゆらぎ吸収）/ date→`YYYY-MM-DD` / bool→bool
  - str は **trim しない**（BQ も空白保持）。**Excel エラー（#N/A 等）は NULL に揃えて吸収**（BQ=文字列 / SF=NULL。数式エラー由来の #N/A は pandas が保持できないため）。
- **設計差の列は exclude**（masking ではなく明示）。例: 実績 `source_sheet_name`（SF=yyyymm / BQ=生シート名）。

## 手順
1. 対象テーブルを **dbtレイヤー別**に確定する（`verify_code.py` の `TABLES` と SF の RAW/STG/INT/MART）。
2. 各テーブルごとに **numerical-verifier サブエージェントへ委譲**（並列可）。サブエージェントは
   `verify_code.py --table <ラベル> --show-diff` を実行し、結果を解釈して
   `docomo_event_sf/docs/numerical_verification/<layer>/<table>.md` を
   `docs/numerical_verification/template.md` に沿って記入する。
3. 全テーブルの判定（OK/NG）を集約して要約する。

### 一括実行（全テーブル）
```bash
cd docomo_event_sf
python tools/verify_code.py            # 全テーブルの一致/差分を一覧表示
python tools/verify_code.py --table 季節指数 --show-diff   # 1テーブル＋差分サンプル
```

## ドキュメントの置き場所（SFのdbtレイヤー基準）
```
docomo_event_sf/docs/numerical_verification/
├── template.md     # ひな形（編集しない）
├── raw/<table>.md  # SF RAW.* ↔ BQ raw_*
├── stg/<table>.md  # SF STG.* ↔ BQ raw_*
├── int/<table>.md  # （今後）SF INT.*
└── mart/<table>.md # （今後）SF MART.*
```
ファイル名は **SF側の物理テーブル名（小文字）** に合わせる。

## 判定基準
- **完全一致**、または **既知の許容差分のみ**（exclude列／#N/A吸収）であれば **OK**。それ以外は **NG**。
- NG の場合は不一致の列・件数・例を必ずドキュメントに残す。
