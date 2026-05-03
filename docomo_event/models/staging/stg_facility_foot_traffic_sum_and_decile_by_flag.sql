SELECT *
FROM
  {{ source('docomo_event_raw', 'raw_facility_foot_traffic_sum_and_decile_by_flag') }}
