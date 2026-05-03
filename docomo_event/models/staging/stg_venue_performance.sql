SELECT
  * EXCEPT (facility_name),
  TRIM(facility_name) AS facility_name
FROM {{ source('docomo_event_raw', 'raw_venue_performance') }}
