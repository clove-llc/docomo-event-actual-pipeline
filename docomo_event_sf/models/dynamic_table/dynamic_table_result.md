# dbt-snowflake × Dynamic Table 検証結果

源泉(seed) → base → mart の dynamic table チェーンで、源泉のデータ変更が下流へ伝播するかを検証した記録。

## 検証時の条件

| 項目 | 値 |
|---|---|
| 実施日 | 2026-06-15 |
| dbt | dbt-core 1.11.8 / dbt-snowflake 1.11.5 |
| 対象スキーマ | `HARATO.DYN`（既存 INT/MART を汚さないよう分離） |
| materialized | `dynamic_table` |
| 源泉 | seed `dyn_source.csv` → `HARATO.DYN.DYN_SOURCE`（通常テーブル） |
| 構成 | seed → `base` → `mart`（dynamic table on dynamic table） |
| snowflake_warehouse | `STREAMLIT_WH` |
| **target_lag** | **`1 minute`**（検証用に最小。自動リフレッシュを短時間で観測するため。本番は要件に応じて延ばす） |
| refresh_mode | **`INCREMENTAL`** |

### 構成図
```
seeds/dynamic_table/dyn_source.csv   源泉(seed) → HARATO.DYN.DYN_SOURCE（通常テーブル）
        │ ref('dyn_source')
        ▼
models/dynamic_table/base.sql        dynamic table → HARATO.DYN.BASE
        │ ref('base')
        ▼
models/dynamic_table/mart.sql        dynamic table → HARATO.DYN.MART
```

### モデル定義（決定的クエリ＝INCREMENTAL 維持）
- `base.sql`: `select id, name from {{ ref('dyn_source') }}`
- `mart.sql`: `select id, name from {{ ref('base') }}`

---

## 1回目（初回ビルド）

操作: `dbt seed --select dyn_source` → `dbt run --select dynamic_table`

源泉 seed は1行だけ。base / mart も同じ1行になる。

**dyn_source.csv（源泉）**
| id | name |
|---:|---|
| 1 | alpha |

**HARATO.DYN.BASE（dynamic table）**
| id | name |
|---:|---|
| 1 | alpha |

**HARATO.DYN.MART（dynamic table）**
| id | name |
|---:|---|
| 1 | alpha |

→ seed → base → mart が依存順に作成され、全て `(1, alpha)` で一致。

---

## 2回目（源泉に行を追加して再実行）

操作: `dyn_source.csv` に `2,beta` と `3,zeta` を追記 → `dbt seed --select dyn_source`（源泉を再ロード）
※ **データ変更なので `--full-refresh` は不要**。あとは target_lag(1分) の自動リフレッシュ、または手動 `ALTER DYNAMIC TABLE ... REFRESH` で反映。

**dyn_source.csv（源泉）**
| id | name |
|---:|---|
| 1 | alpha |
| 2 | beta |
| 3 | zeta |

**HARATO.DYN.BASE（dynamic table）**
| id | name |
|---:|---|
| 1 | alpha |
| 2 | beta |
| 3 | zeta |

**HARATO.DYN.MART（dynamic table）**
| id | name |
|---:|---|
| 1 | alpha |
| 2 | beta |
| 3 | zeta |

→ 源泉の追加行が **base 経由で mart まで自動伝播**。`refresh_mode=INCREMENTAL` のため差分のみ反映。

### 自動リフレッシュの実観測（手動 REFRESH なし）
```
seed 再ロード(id=3 追加)            16:36:59
  ↓ 自動（refresh_trigger=SCHEDULED, 約1分間隔）
BASE 自動リフレッシュ(INCREMENTAL)   16:37:26  → base=[1,2,3]
MART 自動リフレッシュ(INCREMENTAL)   16:37:27  → mart=[1,2,3]
```
→ target_lag=1分なら、源泉変更から **約30秒〜1分で自動的に下流まで反映**された。

---
