"""ローカルの Streamlit アプリを Snowflake (Streamlit in Snowflake) へデプロイ／更新する。

処理:
  1. `.streamlit/secrets.toml` の認証情報で Snowflake に接続（キーペア等）
  2. ステージを作成（無ければ）
  3. アプリファイル（app.py / environment.yml）を PUT でステージへアップロード（OVERWRITE）
  4. `CREATE OR REPLACE STREAMLIT` で SiS アプリを更新

通常は `deploy.sh` 経由で実行する。

使い方:
    python deploy.py [APP_NAME]      # 既定: UPLOADER_XLSX
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).parent
SECRETS = HERE / ".streamlit" / "secrets.toml"
STAGE = "STREAMLIT_STAGE"
UPLOAD_FILES = ["app.py", "sf_common.py", "datasets.py", "environment.yml"]  # ステージ直下へ送る
PKG_DIRS = ["loaders"]  # パッケージ（loaders/*.py）はステージの同名サブディレクトリへ送る
PLACEHOLDERS = {"ORG-ACCOUNT", "USERNAME", "PASSWORD", "ROLE", "WAREHOUSE", "DATABASE", "SCHEMA", ""}


def load_cfg() -> dict:
    if not SECRETS.exists():
        sys.exit(f"❌ {SECRETS} がありません。secrets.toml を用意してください。")
    cfg = tomllib.loads(SECRETS.read_text(encoding="utf-8")).get("snowflake", {})
    if cfg.get("account", "") in PLACEHOLDERS or cfg.get("user", "") in PLACEHOLDERS:
        sys.exit("❌ secrets.toml の account/user が未設定です。")
    return cfg


def connect(cfg: dict):
    import snowflake.connector

    params = {}
    for key in ("account", "user", "password", "role", "authenticator",
                "private_key_file", "private_key_file_pwd", "host",
                "warehouse", "database", "schema"):
        v = cfg.get(key)
        if v and v not in PLACEHOLDERS:
            params[key] = v
    return snowflake.connector.connect(**params)


def main() -> int:
    app_name = (sys.argv[1] if len(sys.argv) > 1 else "UPLOADER_XLSX").upper()
    cfg = load_cfg()
    db = cfg.get("database")
    schema = cfg.get("schema")
    wh = cfg.get("warehouse")
    if not (db and schema and wh):
        sys.exit("❌ secrets.toml に database / schema / warehouse を設定してください。")

    conn = connect(cfg)
    cur = conn.cursor()
    fq_stage = f"{db}.{schema}.{STAGE}"
    stage_path = f"@{fq_stage}/{app_name}"

    print(f"▶ ステージ作成: {fq_stage}")
    cur.execute(f"CREATE STAGE IF NOT EXISTS {fq_stage} "
                f"DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')")

    for f in UPLOAD_FILES:
        local = (HERE / f).resolve()
        if not local.exists():
            print(f"  ⚠ スキップ（無し）: {f}")
            continue
        print(f"▶ アップロード: {f} → {stage_path}")
        cur.execute(f"PUT 'file://{local}' '{stage_path}/' AUTO_COMPRESS=FALSE OVERWRITE=TRUE")

    for pkg in PKG_DIRS:
        pkg_dir = HERE / pkg
        if not pkg_dir.is_dir():
            continue
        for local in sorted(pkg_dir.glob("*.py")):
            print(f"▶ アップロード: {pkg}/{local.name} → {stage_path}/{pkg}")
            cur.execute(f"PUT 'file://{local.resolve()}' '{stage_path}/{pkg}/' "
                        f"AUTO_COMPRESS=FALSE OVERWRITE=TRUE")

    # ディレクトリテーブルを更新（Snowsight のステージ表示を最新化）
    print(f"▶ ステージ更新: ALTER STAGE {fq_stage} REFRESH")
    cur.execute(f"ALTER STAGE {fq_stage} REFRESH")

    print(f"▶ STREAMLIT 作成/更新: {db}.{schema}.{app_name}")
    cur.execute(f"""
        CREATE OR REPLACE STREAMLIT {db}.{schema}.{app_name}
          ROOT_LOCATION = '{stage_path}'
          MAIN_FILE = 'app.py'
          QUERY_WAREHOUSE = '{wh}'
          TITLE = 'Excel → Snowflake Uploader'
    """)

    # アプリURL（Snowsight）を取得
    try:
        cur.execute(f"SHOW STREAMLITS LIKE '{app_name}' IN SCHEMA {db}.{schema}")
        rows = cur.fetchall()
        url_col = [d[0] for d in cur.description].index("url_id") if any(
            d[0] == "url_id" for d in cur.description) else None
        print("\n✅ デプロイ完了")
        print(f"   STREAMLIT: {db}.{schema}.{app_name}")
        print("   Snowsight の Projects → Streamlit から起動できます。")
        if rows and url_col is not None:
            print(f"   url_id: {rows[0][url_col]}")
    except Exception:  # noqa: BLE001
        print("\n✅ デプロイ完了（URL取得はスキップ）")

    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
