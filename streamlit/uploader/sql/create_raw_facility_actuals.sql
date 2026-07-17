DECLARE
    V_INFO_SCHEMA_TABLES STRING;
    V_SQL_BODY STRING;
    V_SQL STRING;

    E_NO_SOURCE_TABLES EXCEPTION
        (-20001, 'RAW_FACILITY_ACTUALS_<YYYYMM> TABLES NOT FOUND');

BEGIN

    V_INFO_SCHEMA_TABLES := 'USERDB_D_P01_LAK' || '.INFORMATION_SCHEMA.TABLES';

    SELECT
        LISTAGG(
            REPLACE(
                REPLACE(
$$
SELECT
    '<SOURCE_SHEET_NAME>' AS SOURCE_SHEET_NAME,
    FLAT."支社名"        AS REGIONAL_OFFICE_NAME,
    FLAT."支店"          AS BRANCH_OFFICE_NAME,
    FLAT."施設名"        AS FACILITY_NAME,
    FLAT."フロア"        AS FLOOR_LABEL,
    FLAT."スペース名"    AS SPACE_NAME,
    FLAT."面積"          AS AREA_RAW,
    FLAT."ヘルパー会社"  AS HELPER_COMPANY_NAME,
    FLAT."スタッフ数"    AS STAFF_COUNT_RAW,
    FLAT."開始日"        AS START_DATE,
    FLAT."終了日"        AS END_DATE,
    TO_DATE(FLAT.__EVENT_DATE_TEXT) AS EVENT_DATE,
    CASE
        WHEN FLAT.__CELL_RAW IN ('＠', '@', '中止', '確認中') THEN NULL
        WHEN FLAT.__CELL_RAW = 'なし' THEN 0
        ELSE ROUND(TRY_TO_DECIMAL(REPLACE(FLAT.__CELL_RAW, ',', ''), 38, 4))
    END::NUMBER(38,0) AS ACTUAL_VALUE
FROM (
    SELECT
        SRC.*,
        F.KEY::STRING AS __EVENT_DATE_TEXT,
        TRIM(F.VALUE::STRING) AS __CELL_RAW
    FROM (
        SELECT
            T.*,
            OBJECT_CONSTRUCT(*) AS __ROW_OBJ
        FROM <TABLE_FQN> T
    ) SRC,
    LATERAL FLATTEN(INPUT => SRC.__ROW_OBJ) F
    WHERE F.KEY::STRING RLIKE '[0-9]{4}-[0-9]{2}-[0-9]{2}'
      AND SRC."施設名" IS NOT NULL
) FLAT
WHERE FLAT.__CELL_RAW <> ''
  AND (
        FLAT.__CELL_RAW IN ('＠', '@', '中止', '確認中', 'なし')
        OR TRY_TO_DECIMAL(REPLACE(FLAT.__CELL_RAW, ',', ''), 38, 4) IS NOT NULL
      )
$$,
                    '<SOURCE_SHEET_NAME>',
                    RIGHT(TABLE_NAME, 6)
                ),
                '<TABLE_FQN>',
                '"' || TABLE_CATALOG || '"."' ||
                TABLE_SCHEMA || '"."' ||
                TABLE_NAME || '"'
            ),
            ' UNION ALL '
        ) WITHIN GROUP (ORDER BY TABLE_NAME)
    INTO :V_SQL_BODY
    FROM IDENTIFIER(:V_INFO_SCHEMA_TABLES)
    WHERE TABLE_SCHEMA = 'USER_SMCB_01'
      AND TABLE_NAME ILIKE 'RAW_FACILITY_ACTUALS_2%'
      AND TABLE_TYPE = 'BASE TABLE';

    IF (V_SQL_BODY IS NULL OR V_SQL_BODY = '') THEN
        RAISE E_NO_SOURCE_TABLES;
    END IF;

    V_SQL :=
        'CREATE OR REPLACE TABLE ' ||
        'USERDB_D_P01_LAK.USER_SMCB_01.RAW_FACILITY_ACTUALS' ||
        ' AS ' ||
        V_SQL_BODY;

    EXECUTE IMMEDIATE V_SQL;

END;