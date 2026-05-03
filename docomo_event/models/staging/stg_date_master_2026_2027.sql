SELECT *
FROM {{ source('docomo_event_raw', 'raw_date_master_2026_2027') }}
