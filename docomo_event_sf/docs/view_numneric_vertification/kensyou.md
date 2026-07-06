# 数値検証 使用SQL・結果ハッシュ一覧（BQ ↔ Snowflake DOCOMO_DB）

- 実施日: 2026-07-04
- 比較エンジン: `docomo_event_sf/tools/verify_code.py`
- 対象: 27テーブル（raw 8 / stg 8 / int 10 / mart 1）

## 1. 検証時に利用したSQL

検証は次の3種類のSQLのみで行う（**両DBともSELECTのみ・書き込みなし**）。

### ① 比較列の導出（BigQuery・BQカラムベース）
比較する列とその型は、BQ の INFORMATION_SCHEMA から自動導出する（手書き定義なし）。

```sql
SELECT column_name, data_type
FROM `digital-well-456700-i9.<dataset>.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = '<table>'
ORDER BY ordinal_position;
```

### ② BigQuery データ取得
①で得た列のうち **Snowflake 側にも存在する列だけ**を指定して取得する
（SFに無いBQ列は警告のうえ比較除外。例: mart の `p50_seasonal`）。

```sql
SELECT <BQ列のうちSFと共通の列, ...>
FROM `digital-well-456700-i9.<dataset>.<table>`;
```

### ③ Snowflake データ取得
```sql
SELECT * FROM <SF_FQTN>;
```
取得後、列名を小文字化し、②と同じ共通列のみを比較に使用する。

### 比較方法（SQLではなくPython側）
- **多重集合（Counter）**で行レベル突合（ORDER BY 不要・重複行も正確に比較）。
- 正規化は型表現差の吸収のみ: num→float(小数9桁丸め) / date→`YYYY-MM-DD` / bool→bool /
  str はそのまま（trimしない・Excelエラー `#N/A` 等→NULL）。

### ハッシュ値の定義
正規化後の全行を **順序非依存** でハッシュ化したもの。

```
multiset_hash = MD5( sorted("<行タプルrepr>|<出現回数>") を改行連結 )
```
- **BQとSFのハッシュが一致 ＝ 正規化後の全行（重複数含む）が完全一致**。
- 差分が1行でもあればハッシュは不一致になる。

### 補足SQL（mart `is_excluded` の等価性確認に使用）
```sql
-- 値分布
SELECT is_excluded, COUNT(*) FROM `digital-well-456700-i9.docomo_event_mart.fact_facility_performance_slots` GROUP BY 1;
SELECT IS_EXCLUDED,  COUNT(*) FROM DOCOMO_DB.MART.FACT_FACILITY_PERFORMANCE_SLOTS GROUP BY 1;
-- TRUE の施設集合
SELECT DISTINCT facility_code FROM `digital-well-456700-i9.docomo_event_mart.fact_facility_performance_slots` WHERE is_excluded = TRUE;
SELECT DISTINCT FACILITY_CODE  FROM DOCOMO_DB.MART.FACT_FACILITY_PERFORMANCE_SLOTS WHERE IS_EXCLUDED = TRUE;
-- 結果: TRUE 50,370行・23施設が完全一致（BQ=NULL/SF=FALSE は表現差のみ）
```

## 2. テーブル別 使用SQL（②③のFROM先）と結果ハッシュ

### raw 層（BQ `docomo_event_raw` ↔ SF `HARATO.RAW`）— 全て一致

| # | テーブル | BQ FROM | SF FROM | 件数 | ハッシュ（BQ = SF） | 除外列 |
|--|---|---|---|--:|---|---|
| 1 | 人流デシル | `docomo_event_raw.raw_facility_foot_traffic_avg_and_decile_by_flag` | `HARATO.RAW.RAW_FACILITY_FOOT_TRAFFIC_AVG_AND_DECILE_BY_FLAG` | 794 | `bef466c171bf1b811df7190528edc0b3` ✅ | — |
| 2 | 季節指数 | `docomo_event_raw.raw_facility_daily_deviation_zscore` | `HARATO.RAW.RAW_FACILITY_DAILY_DEVIATION_ZSCORE` | 289,810 | `67a1e060a4e4ade82082d98f5c298dbe` ✅ | — |
| 3 | 実績データ | `docomo_event_raw.raw_facility_actuals` | `HARATO.RAW.RAW_FACILITY_ACTUALS` | 72,141 | `893617f6b2cf9e368c75542e004f4d7a` ✅ | source_sheet_name |
| 4 | 日付マスタ | `docomo_event_raw.raw_date_master` | `HARATO.RAW.RAW_DATE_MASTER` | 730 | `6b358516c1ce0d4523373bef38c4233b` ✅ | — |
| 5 | 施設マスタ | `docomo_event_raw.raw_facility_master` | `HARATO.RAW.RAW_FACILITY_MASTER` | 794 | `29da172aaf819f98b982595373797f9d` ✅ | branch_office |
| 6 | 施設名マッピング | `docomo_event_raw.raw_facility_name_mappings` | `HARATO.RAW.RAW_FACILITY_NAME_MAPPINGS` | 935 | `df3e6bf2373aed5b23a2f5ab62c6bad7` ✅ | — |
| 7 | 除外施設マスタ | `docomo_event_raw.raw_excluded_facility_master` | `HARATO.RAW.RAW_EXCLUDED_FACILITY_MASTER` | 8 | `9e56a486148f6cb6aac4d7da80cd321e` ✅ | — |
| 8 | 目標CPAマスタ | `docomo_event_raw.raw_facility_target_cpa_master` | `HARATO.RAW.RAW_FACILITY_TARGET_CPA_MASTER` | 648 | `36f08f10b7ad6e520dbda822ce4cbaf6` ✅ | — |

### stg 層（BQ `docomo_event_staging` ↔ SF `DOCOMO_DB.STG`・VIEW）— 全て一致

| # | テーブル | BQ FROM | SF FROM | 件数 | ハッシュ（BQ = SF） | 除外列 |
|--|---|---|---|--:|---|---|
| 9 | 人流デシル | `docomo_event_staging.stg_facility_foot_traffic_avg_and_decile_by_flag` | `DOCOMO_DB.STG.STG_FACILITY_FOOT_TRAFFIC_AVG_AND_DECILE_BY_FLAG` | 794 | `bef466c171bf1b811df7190528edc0b3` ✅ | — |
| 10 | 季節指数 | `docomo_event_staging.stg_facility_daily_deviation_zscore` | `DOCOMO_DB.STG.STG_FACILITY_DAILY_DEVIATION_ZSCORE` | 289,810 | `67a1e060a4e4ade82082d98f5c298dbe` ✅ | — |
| 11 | 実績データ | `docomo_event_staging.stg_facility_actuals` | `DOCOMO_DB.STG.STG_FACILITY_ACTUALS` | 72,141 | `800a2c9ef63cadaad5bebba5d7693bec` ✅ | source_sheet_name |
| 12 | 日付マスタ | `docomo_event_staging.stg_date_master` | `DOCOMO_DB.STG.STG_DATE_MASTER` | 730 | `6b358516c1ce0d4523373bef38c4233b` ✅ | — |
| 13 | 施設マスタ | `docomo_event_staging.stg_facility_master` | `DOCOMO_DB.STG.STG_FACILITY_MASTER` | 794 | `0470c2ecdfa03a3fa34963782c31eb7e` ✅ | branch_office |
| 14 | 施設名マッピング | `docomo_event_staging.stg_facility_name_mappings` | `DOCOMO_DB.STG.STG_FACILITY_NAME_MAPPINGS` | 935 | `df3e6bf2373aed5b23a2f5ab62c6bad7` ✅ | — |
| 15 | 除外施設マスタ | `docomo_event_staging.stg_excluded_facility_master` | `DOCOMO_DB.STG.STG_EXCLUDED_FACILITY_MASTER` | 8 | `9e56a486148f6cb6aac4d7da80cd321e` ✅ | — |
| 16 | 目標CPAマスタ | `docomo_event_staging.stg_facility_target_cpa_master` | `DOCOMO_DB.STG.STG_FACILITY_TARGET_CPA_MASTER` | 648 | `e56567736c6b7d980598e39f1073751d` ✅ | — |

### int 層（BQ `docomo_event_intermediate` ↔ SF `DOCOMO_DB.INT`・VIEW）

| # | テーブル | BQ FROM / SF FROM | 件数 | ハッシュ BQ | ハッシュ SF | 一致 | 差分行（既知） |
|--|---|---|--:|---|---|:--:|---|
| 17 | 実績(int) | `int_facility_actuals` / `DOCOMO_DB.INT.INT_FACILITY_ACTUALS` | 72,087 | `94eccc4888fb279faaa06d2121ca331c` | 同左 | ✅ | 0（除外: source_sheet_name） |
| 18 | 日別実績 | `int_facility_daily_actual` / `DOCOMO_DB.INT.INT_FACILITY_DAILY_ACTUAL` | 30,472 | `90db3ea988a4283f4b9cb15c6c26b98b` | 同左 | ✅ | 0（除外: branch_office） |
| 19 | ベンチ期間 | `int_benchmark_periods` / `DOCOMO_DB.INT.INT_BENCHMARK_PERIODS` | 3 | `bf07acaddbe91183849619e1bff9097a` | 同左 | ✅ | 0 |
| 20 | デシルマッピング | `int_facility_event_decile_mapping` / `DOCOMO_DB.INT.INT_FACILITY_EVENT_DECILE_MAPPING` | 7,146 | `f3c8619819956ae3e410dfbb56a71680` | 同左 | ✅ | 0 |
| 21 | デシル平均実績 | `int_facility_event_decile_avg_actual` / `DOCOMO_DB.INT.INT_FACILITY_EVENT_DECILE_AVG_ACTUAL` | 4,184 | `d3480196258f5eaa09e31df8096e7a8f` | `37eab1b2cf486a47ccccf261d015ef1d` | ✗ | 9（FLOAT境界差・除外: branch_office） |
| 22 | デシルベンチ | `int_event_decile_benchmark` / `DOCOMO_DB.INT.INT_EVENT_DECILE_BENCHMARK` | 210 | `192305a902ec61dad6d247f557456201` | `925d25622fb7d506b297ff5d100bf69c` | ✗ | 9（FLOAT境界差） |
| 23 | 月週フラグZ | `int_facility_monthly_weekday_dateflag_deviation_zscore` / `DOCOMO_DB.INT.INT_FACILITY_MONTHLY_WEEKDAY_DATEFLAG_DEVIATION_ZSCORE` | 96,074 | `028074f0112bc3c576016fa2022d6f5b` | `b3381495bc4296f6812ca0a749b73528` | ✗ | 583（FLOAT境界差 ±0.1） |
| 24 | 月フラグZ | `int_facility_monthly_dateflag_deviation_zscore` / `DOCOMO_DB.INT.INT_FACILITY_MONTHLY_DATEFLAG_DEVIATION_ZSCORE` | 30,966 | `5820ab1a6b114042d2214249ab2b3bbe` | `c0f05b800fde3b42b64bae268c3d8e12` | ✗ | 1,489（FLOAT境界差 ±0.1） |
| 25 | 計画スナップショット | `int_facility_event_planning_snapshot` / `DOCOMO_DB.INT.INT_FACILITY_EVENT_PLANNING_SNAPSHOT` | 21,438 | `fe11fd964794b8e5a71b5b75a58918ba` | `6217773197ed8027c6b2ede5e707f957` | ✗ | 720（分位点±1伝播＋タイル増幅・除外: branch_office） |
| 26 | 施設別目標CPA | `int_facility_target_cpa_by_facility` / `DOCOMO_DB.INT.INT_FACILITY_TARGET_CPA_BY_FACILITY` | 639 | `33d0a09f75257fd739aff927ebdf2348` | `19cb7b9e1e0c00c954a8a6ff8aa26bfc` | ✗ | 1（cpa 小数6桁の型精度差 ≈4.4e-7） |

### mart 層（BQ `docomo_event_mart` ↔ SF `DOCOMO_DB.MART`・VIEW）

| # | テーブル | BQ FROM / SF FROM | 件数 | ハッシュ BQ | ハッシュ SF | 一致 | 差分行（既知） |
|--|---|---|--:|---|---|:--:|---|
| 27 | 実績スロットFact | `fact_facility_performance_slots` / `DOCOMO_DB.MART.FACT_FACILITY_PERFORMANCE_SLOTS` | 1,738,860 | `af9f0723838d6eca18f7799aa68f6837` | `dfb69b89503347f1e5e5fda3aff2d2f5` | ✗ | 17,949=1.03%（target系4列のFLOAT境界差のみ。除外: branch_office / is_excluded。`p50_seasonal` はSFに無く比較除外） |

## 3. 除外列（設計差）の一覧

| 列 | 対象テーブル | 理由 |
|---|---|---|
| `source_sheet_name` | 実績データ（raw/stg/int） | SF=正規化 yyyymm（202510）/ BQ=生シート名（2025.1）。データ本体は一致 |
| `branch_office` | 施設マスタ（raw/stg）・日別実績・デシル平均実績・計画スナップショット・mart | SF=拠点略号プレフィックス除去（BQ「神）神奈川支店」→SF「神奈川支店」） |
| `is_excluded` | mart | BQ=除外マスタ未マッチはNULL / SF=FALSEに正規化。TRUE 50,370行・23施設の一致をSQLで確認済み |

## 4. 判定サマリ

- ハッシュ一致（完全一致）: **20/27**（raw 8・stg 8・int 4）
- ハッシュ不一致: 7テーブル。ただし**すべて既知の許容差分**
  （FLOAT演算順序差 9/9/583/1,489/720/17,949 行＋CPA型精度 1 行）で判定は全て **OK**。
- 再現コマンド: `cd docomo_event_sf && python tools/verify_code.py`（層別: `--layer raw|stg|int|mart`）
