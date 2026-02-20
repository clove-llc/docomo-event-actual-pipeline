from google.cloud import bigquery

FACILITY_DAILY_DEVIATION_ZSCORE_SCHEMA = [
    bigquery.SchemaField("date", "DATE", description="日付"),
    bigquery.SchemaField("facility_code", "INTEGER", description="施設コード"),
    bigquery.SchemaField("facility_name", "STRING", description="施設名"),
    bigquery.SchemaField("z_score", "FLOAT", description="偏差値ベースのZスコア"),
    bigquery.SchemaField("month", "INTEGER", description="月番号"),
    bigquery.SchemaField("weekday_monthly", "INTEGER", description="週番号（月）"),
    bigquery.SchemaField("date_flag", "STRING", description="日付フラグ"),
]
