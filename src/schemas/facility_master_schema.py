from google.cloud import bigquery

FACILITY_MASTER_SCHEMA = [
    bigquery.SchemaField("no", "INTEGER", description="No"),
    bigquery.SchemaField("check", "STRING", description="Check"),
    bigquery.SchemaField(
        "retail_data_sheet_name", "STRING", description="量販店データシートの名称"
    ),
    bigquery.SchemaField(
        "search_keyword_competitor_map",
        "STRING",
        description="検索ワード（他社対抗MAP名）",
    ),
    bigquery.SchemaField(
        "display_facility_name", "STRING", description="表示施設名（全体管理簿）"
    ),
    bigquery.SchemaField("po_level", "STRING", description="POレベル"),
    bigquery.SchemaField("facility_category", "STRING", description="施設カテゴリ"),
    bigquery.SchemaField("regional_office", "STRING", description="支社"),
    bigquery.SchemaField("branch_office", "STRING", description="支店"),
    bigquery.SchemaField(
        "facility_address_raw", "STRING", description="施設住所（不完全のため検索不可）"
    ),
    bigquery.SchemaField(
        "inshop_store_name", "STRING", description="インショップ店舗名"
    ),
    bigquery.SchemaField("satellite", "STRING", description="サテライト"),
    bigquery.SchemaField(
        "satellite_parent_store", "STRING", description="サテライト母体店舗"
    ),
    bigquery.SchemaField("satellite_code", "STRING", description="サテライトコード"),
    bigquery.SchemaField("retail_store_1", "STRING", description="量販店1"),
    bigquery.SchemaField("retail_store_2", "STRING", description="量販店2"),
    bigquery.SchemaField("retail_store_3", "STRING", description="量販店3"),
    bigquery.SchemaField(
        "retail_internal_code_1", "STRING", description="量販店内部コード1"
    ),
    bigquery.SchemaField(
        "retail_internal_code_2", "STRING", description="量販店内部コード2"
    ),
    bigquery.SchemaField(
        "retail_internal_code_3", "STRING", description="量販店内部コード3"
    ),
    bigquery.SchemaField(
        "has_ds_or_satellite", "STRING", description="DS or サテライトあり"
    ),
    bigquery.SchemaField(
        "has_ds_or_satellite_bool",
        "BOOLEAN",
        description="DS or サテライトあり_BOOLEAN化",
    ),
    bigquery.SchemaField("ds_flag", "STRING", description="DS"),
    bigquery.SchemaField("ds_bool", "BOOLEAN", description="DS_BOOLEAN化"),
    bigquery.SchemaField("st_flag", "STRING", description="ST"),
    bigquery.SchemaField("st_bool", "BOOLEAN", description="ST_BOOLEAN化"),
    bigquery.SchemaField("retail_flag", "STRING", description="量販"),
    bigquery.SchemaField("retail_bool", "BOOLEAN", description="量販_BOOLEAN化"),
    bigquery.SchemaField("softbank_flag", "STRING", description="SB"),
    bigquery.SchemaField("softbank_bool", "BOOLEAN", description="SB_BOOLEAN化"),
    bigquery.SchemaField("au_flag", "STRING", description="au"),
    bigquery.SchemaField("au_bool", "BOOLEAN", description="au_BOOLEAN化"),
    bigquery.SchemaField("rakuten_mobile_flag", "STRING", description="楽天モバイル"),
    bigquery.SchemaField(
        "rakuten_mobile_bool", "BOOLEAN", description="楽天モバイル_BOOLEAN化"
    ),
    bigquery.SchemaField("facility_group", "STRING", description="施設グループ"),
    bigquery.SchemaField("notes", "STRING", description="備考"),
    bigquery.SchemaField("facility_category_2", "STRING", description="施設カテゴリ2"),
    bigquery.SchemaField("business_floor_area", "INTEGER", description="営業面積"),
    bigquery.SchemaField("tenant_count", "INTEGER", description="テナント数"),
]
