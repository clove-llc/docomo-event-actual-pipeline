SELECT *
FROM {{ source('docomo_event_raw', 'raw_facility_daily_deviation_zscore') }}
