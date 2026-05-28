SELECT *
FROM {{ source('docomo_event_raw', 'raw_date_master') }}
