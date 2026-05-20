SELECT *
FROM
  {{ source('docomo_event_raw', 'raw_facility_foot_traffic_avg_and_decile_by_flag') }}
