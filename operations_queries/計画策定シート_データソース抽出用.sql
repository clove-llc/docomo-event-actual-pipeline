/* 
============================================================

計画策定シート用のデータソース抽出用のクエリです。

- 実績値のAVG後の粒度：過去実績期間×施設×日付フラグ
- デシルランクの粒度：施設×日付フラグ
- 分布値の粒度：過去実績期間×日付フラグ×デシルランク
- 目標値の粒度：過去実績期間×施設×日付フラグ

============================================================
*/
SELECT
    PERIOD_START_DATE AS "過去実績対象期間_開始日",
    PERIOD_END_DATE AS "過去実績対象期間_終了日",
    FACILITY_CODE AS "施設コード",
    FACILITY_NAME AS "施設名",
    PO_LEVEL,
    REGIONAL_OFFICE AS "支社",
    BRANCH_OFFICE AS "支店",
    DATE AS "日付",
    MONTH AS "月",
    WEEK_NUMBER_MONTHLY AS "月内週番号",
    DATE_FLAG AS "日付フラグ",
    DECILE_RANK AS "デシルランク",
    AVG_ACTUAL AS "過去実績値",
    STANDARD_TARGET AS "標準目標値",
    CHALLENGE_TARGET AS "チャレンジ目標値",
    Z_SCORE AS "季節指数",
    STANDARD_TARGET_SEASONAL AS "標準目標値_季節指数加味",
    CHALLENGE_TARGET_SEASONAL AS "チャレンジ目標値_季節指数加味"
FROM USERDB_D_P01_LAK.USER_SMCB_01.FACT_FACILITY_PERFORMANCE_SLOTS_TABLE -- 「データベース名」はここで変更する。
WHERE BENCHMARK_PERIOD_KEY = '2025_10_2026_02' -- 「過去実績期間」はここで変更する。
  AND "DATE" BETWEEN '2026-04-01'::date AND '2027-03-31'::date -- 「目標値を出力する期間」はここで変更する。