/*
============================================================

RAW層のテーブル（RAW_から始まるテーブル）が更新された際に実行するクエリです。
最終マートビューをテーブル化します。
（最終マートビューのままだと、Excelワークブックビルダーでデータを取得する際に時間がかかってしまうため）

============================================================
*/
CREATE OR REPLACE TABLE USERDB_B_P01_LAK.USER_SMCB_01.FACT_FACILITY_PERFORMANCE_SLOTS_TABLE AS (
    SELECT
        *
    FROM USERDB_B_P01_LAK.USER_SMCB_01.FACT_FACILITY_PERFORMANCE_SLOTS_VIEW
)