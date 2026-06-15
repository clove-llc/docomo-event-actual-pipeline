SELECT
  * EXCEPT (facility_name),
  REPLACE(TRIM(facility_name), '・', '･') AS facility_name
FROM {{ source('docomo_event_raw', 'raw_facility_target_cpa_master') }}
