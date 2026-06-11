{#-
  BQ int_facility_event_decile_mapping のミラー。
  stg_facility_foot_traffic_avg_and_decile_by_flag（横持ち9フラグのデシル）を縦持ち化。
  BQ の UNPIVT(... AS '日本語') は Snowflake で素直に書けないため、フラグ分の UNION ALL で再現する。
-#}
{%- set flags = [
    ('GW', 'gw'),
    ('お盆', 'obon'),
    ('三連休', 'three_day_holiday'),
    ('正月', 'new_year'),
    ('通常土日', 'regular_weekend'),
    ('年末', 'year_end'),
    ('飛び石祝日', 'bridge_holiday'),
    ('平日', 'weekday'),
    ('ブラックフライデー', 'black_friday'),
] -%}

with unpivoted as (
    {% for jp, en in flags -%}
    select
        facility_code,
        facility_name,
        '{{ jp }}' as date_flag,
        {{ en }}_decile_rank as decile_rank
    from {{ ref('stg_facility_foot_traffic_avg_and_decile_by_flag') }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
)
select
    facility_code,
    facility_name,
    date_flag,
    decile_rank
from unpivoted
where decile_rank is not null
