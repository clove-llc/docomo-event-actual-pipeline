from google.cloud import bigquery

DATE_MASTER_SCHEMA = [
    bigquery.SchemaField("date", "DATE", description="日付"),
    bigquery.SchemaField("year_month", "STRING", description="年月"),
    bigquery.SchemaField(
        "week_number_yearly", "INTEGER", description="週番号（月間_1-52（53））"
    ),
    bigquery.SchemaField(
        "week_number_monthly", "INTEGER", description="週番号（月間_1-4（5））"
    ),
    bigquery.SchemaField("weekday_name", "STRING", description="曜日"),
    bigquery.SchemaField("holiday_name", "STRING", description="祝日名"),
    bigquery.SchemaField("is_holiday", "BOOLEAN", description="祝日フラグ"),
    bigquery.SchemaField(
        "weekday_holiday_weekend", "STRING", description="平日/休日（土日のみ）"
    ),
    bigquery.SchemaField(
        "weekday_holiday_with_holiday", "STRING", description="平日/休日（祝日加味）"
    ),
    bigquery.SchemaField("is_offday", "BOOLEAN", description="休日フラグ"),
    bigquery.SchemaField("date_type", "STRING", description="日付種別"),
    bigquery.SchemaField("event_type", "STRING", description="イベント種別"),
]
