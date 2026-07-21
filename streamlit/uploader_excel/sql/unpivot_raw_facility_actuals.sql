/* ============================================================================
   横持ち RAW_FACILITY_ACTUALS_202504 → 縦持ち RAW_FACILITY_ACTUALS（単月・仕様準拠）

   横持ちの日付列は VARCHAR で原文保持されている前提（＠/中止/なし/不明/空/数値）。
   縦持ち化(melt)後の「日付実績」を、テーブル定義書の仕様に従ってクレンジングする:

     - 空セル（完全未入力）           → 行削除（出力しない）
     - 前後空白を TRIM
     - ＠ / @ / 中止 / 確認中          → NULL（行は残す。NULLは意味を持つ値として保持）
     - なし                           → 0（実績ゼロ）
     - カンマ除去のうえ数値（Int64）
     - 上記以外の文字（不明 等）       → 行削除（数値でもステータスでもないため）

   出力13列は docs/テーブル定義書.xlsx「raw_facility_actuals」準拠。
   動的な日付列は OBJECT_CONSTRUCT(*) + LATERAL FLATTEN で unpivot（値NULL=空セルは自動除外）。
   ============================================================================ */

CREATE OR REPLACE TABLE HARATO.STREAMLIT_UPLODER_XLSX.RAW_FACILITY_ACTUALS AS
WITH src AS (
  SELECT t.*, OBJECT_CONSTRUCT(*) AS obj
  FROM HARATO.STREAMLIT_UPLODER_XLSX.RAW_FACILITY_ACTUALS_202504 t
),
flat AS (
  SELECT src.*, f.key AS k, TRIM(f.value::string) AS raw
  FROM src, LATERAL FLATTEN(input => src.obj) f
  WHERE f.key RLIKE '[0-9]{4}-[0-9]{2}-[0-9]{2}'   -- 日付列だけ（固定列・latest_updated_atは除外）
    AND src."施設名" IS NOT NULL                    -- 施設名が空の行は対象外
)
SELECT
  '202504'              AS source_sheet_name,
  "支社名"              AS regional_office_name,
  "支店"                AS branch_office_name,
  "施設名"              AS facility_name,
  "フロア"              AS floor_label,
  "スペース名"          AS space_name,
  "面積"                AS area_raw,
  "ヘルパー会社"        AS helper_company_name,
  "スタッフ数"          AS staff_count_raw,
  "開始日"              AS start_date,
  "終了日"              AS end_date,
  TO_DATE(k)            AS event_date,
  CASE
    WHEN raw IN ('＠', '@', '中止', '確認中') THEN NULL    -- ステータス → NULL（行は残す）
    WHEN raw = 'なし' THEN 0                               -- 実績ゼロ
    ELSE ROUND(TRY_TO_DECIMAL(REPLACE(raw, ',', ''), 38, 4))
  END::NUMBER(38,0)     AS actual_value
FROM flat
WHERE raw <> ''                                            -- 空セルは除外（完全未入力）
  AND ( raw IN ('＠', '@', '中止', '確認中', 'なし')
        OR TRY_TO_DECIMAL(REPLACE(raw, ',', ''), 38, 4) IS NOT NULL )  -- 不明/その他文字は除外
;
