# 実績データ アップローダ

`実績データ.xlsx` の月別シートを横持ちのまま Snowflake へロードする Streamlit アプリ。
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
- 型: `No`→NUMBER ／ `開始日`・`終了日`→DATE ／ 日付列→NUMBER(38,0) ／
  `面積`・`スタッフ数`・`実施日数` ほか→VARCHAR（表記が混在するため raw は原文保持）。
- 監査列 `latest_updated_at`（TIMESTAMP_NTZ, `DEFAULT CURRENT_TIMESTAMP()`）を付与し、
  最後にロード（CREATE OR REPLACE）した時刻を記録する。

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
