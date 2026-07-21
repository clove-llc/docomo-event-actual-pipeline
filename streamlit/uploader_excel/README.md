# Snowflake アップローダ

Excel を Snowflake へロードする Streamlit アプリ。上部のセレクタで対象を選ぶ:
- **実績データ**: `実績データ.xlsx` の月別シートを横持ちのまま `raw_facility_actuals_<yyyymm>` へ。
- **日付マスタ**: `日付マスタ.xlsx` の「日付マスタ」シート（英語物理名は2行目）を `RAW_DATE_MASTER` へ。
- **季節指数マスタ**: `季節指数マスタ.xlsx` の「01_日別施設別（SENSE）」シート（固定）を横持ちのまま
  `RAW_FACILITY_SEASONAL_DAILY` へ（施設コード/施設名/年間平均値＋365日の日次指数）。
- **施設マスタ**: `施設マスタ.xlsx` の「facility_master」シート（固定・英語物理名は2行目）を**全39列raw**で
  `RAW_FACILITY_MASTER` へ（facility_code=NUMBER／`*_bool`=BOOLEAN／その他VARCHAR原文・コードの先頭ゼロ保持）。
- **施設名マッピングマスタ**: `施設名マッピングマスタ.xlsx` の同名シート（固定・英語物理名は2行目）を
  `RAW_FACILITY_NAME_MAPPINGS` へ（`original_name` / `mapped_name` の2列・VARCHAR）。
- **人流・デシルマスタ**: `人流・デシルマスタ.xlsx` の「01_日別施設別（SENSE）」シート（固定・ヘッダーは1行目）を
  横持ちのまま `RAW_FACILITY_FOOT_TRAFFIC_DAILY` へ（施設コード/施設名/年間平均値＋365日の日次値）。

ローカルで開発し、`deploy.sh` で Streamlit in Snowflake (SiS) へ反映する。

---

## 環境構築

### 1. 依存パッケージ
```bash
cd streamlit/uploader
pip install -r requirements.txt
```

### 2. 認証情報（キーペア認証）
RSA 鍵ペアを生成:
```bash
mkdir -p ~/.snowflake && cd ~/.snowflake && \
  openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out clove_dcc.p8 -nocrypt && \
  openssl rsa -in clove_dcc.p8 -pubout -out clove_dcc.pub && \
  chmod 600 clove_dcc.p8
```
公開鍵の本文を取得:
```bash
grep -v "PUBLIC KEY" ~/.snowflake/clove_dcc.pub | tr -d '\n'; echo
```
Snowflake（Snowsight）でユーザーに登録:
```sql
ALTER USER <USER> SET RSA_PUBLIC_KEY='<上で取得した文字列>';
```

### 3. secrets.toml
`.streamlit/secrets.toml.example` をコピーして実値を記入:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
`account / user / role / warehouse / database / schema / private_key_file` を設定する
（`secrets.toml` と秘密鍵 `*.p8` は `.gitignore` 済み＝コミットされない）。

### 4. ローカル起動
```bash
streamlit run app.py          # http://localhost:8501
```
`実績データ.xlsx` をアップロード → 月別シートを選択 → 「🚀 CREATE OR REPLACE TABLE してアップロード」。

- ヘッダーは4行目固定で自動認識（手動調整不要）。
- 固定13列は日本語名そのまま、日付列はシートごとに**動的に取得**（列名 `YYYY-MM-DD`）。
- アップロードのたびに `CREATE OR REPLACE TABLE raw_facility_actuals_<yyyymm>` で作り直す。
- 型: `No`→NUMBER ／ `開始日`・`終了日`→DATE ／ **日付列・`面積`・`スタッフ数`・`実施日数` ほか→VARCHAR**。
  raw は**原文のまま保持**（`＠`/`中止`/`なし`/`不明`/空/カンマ等）。クレンジング（縦持ち化時の正規化）は
  `sql/unpivot_raw_facility_actuals.sql`（および `sql/dbt/`）の縦持ちSQL側で実施する。
- 監査列 `latest_updated_at`（TIMESTAMP_NTZ, `DEFAULT CURRENT_TIMESTAMP()`）を付与し、
  最後にロード（CREATE OR REPLACE）した時刻を記録する。

### 縦持ち化（横持ち→raw_facility_actuals）
`sql/unpivot_raw_facility_actuals.sql` … 単月の縦持ちSQL（仕様準拠のクレンジング）。
`sql/dbt/` … dbtでの実装（for で全月を unpivot＋UNION ALL）。
クレンジング規則: 空→行削除 / TRIM / `＠`・`@`・`中止`・`確認中`→NULL（行は残す） / `なし`→0 /
カンマ除去のうえ Int64 / `不明`等その他→行削除。

---

## デプロイ（Snowflake へ更新）

開発が一段落したら、`deploy.sh` で SiS アプリを作成／更新する。
```bash
cd streamlit/uploader
./deploy.sh                 # 既定アプリ名: UPLOADER_XLSX
./deploy.sh MY_APP_NAME     # アプリ名を指定する場合
```
処理内容: ステージ作成 → `app.py` / `sf_common.py` / `environment.yml` をアップロード → `CREATE OR REPLACE STREAMLIT`。
完了後、**Snowsight → Projects → Streamlit** から起動できる。

> 前提: `secrets.toml` 設定済み・`pip install -r requirements.txt` 済み・`CREATE STREAMLIT` 権限があること。
