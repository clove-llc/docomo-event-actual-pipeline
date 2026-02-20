from google.cloud import bigquery

FACILITY_FOOT_TRAFFIC_SUM_AND_DECILE_BY_FLAG_SCHEMA = [
    bigquery.SchemaField("facility_code", "INTEGER", description="施設コード"),
    bigquery.SchemaField("facility_name", "STRING", description="施設名"),
    bigquery.SchemaField("gw_foot_traffic_total", "INTEGER", description="GW人流合計"),
    bigquery.SchemaField(
        "obon_foot_traffic_total", "INTEGER", description="お盆人流合計"
    ),
    bigquery.SchemaField(
        "three_day_holiday_foot_traffic_total", "INTEGER", description="三連休人流合計"
    ),
    bigquery.SchemaField(
        "new_year_foot_traffic_total", "INTEGER", description="正月人流合計"
    ),
    bigquery.SchemaField(
        "regular_weekend_foot_traffic_total", "INTEGER", description="通常土日人流合計"
    ),
    bigquery.SchemaField(
        "year_end_foot_traffic_total", "INTEGER", description="年末人流合計"
    ),
    bigquery.SchemaField(
        "bridge_holiday_foot_traffic_total", "INTEGER", description="飛び石祝日人流合計"
    ),
    bigquery.SchemaField(
        "weekday_foot_traffic_total", "INTEGER", description="平日人流合計"
    ),
    bigquery.SchemaField(
        "black_friday_foot_traffic_total",
        "INTEGER",
        description="ブラックフライデー人流合計",
    ),
    bigquery.SchemaField("gw_decile_rank", "INTEGER", description="GWデシル区分"),
    bigquery.SchemaField("obon_decile_rank", "INTEGER", description="お盆デシル区分"),
    bigquery.SchemaField(
        "three_day_holiday_decile_rank", "INTEGER", description="三連休デシル区分"
    ),
    bigquery.SchemaField(
        "new_year_decile_rank", "INTEGER", description="正月デシル区分"
    ),
    bigquery.SchemaField(
        "regular_weekend_decile_rank", "INTEGER", description="通常土日デシル区分"
    ),
    bigquery.SchemaField(
        "year_end_decile_rank", "INTEGER", description="年末デシル区分"
    ),
    bigquery.SchemaField(
        "bridge_holiday_decile_rank", "INTEGER", description="飛び石祝日デシル区分"
    ),
    bigquery.SchemaField(
        "weekday_decile_rank", "INTEGER", description="平日デシル区分"
    ),
    bigquery.SchemaField(
        "black_friday_decile_rank",
        "INTEGER",
        description="ブラックフライデーデシル区分",
    ),
]
