{#-
  s2: 02_施設別日別構成比。各日の SENSE 値 ÷ 施設の年間合計 ＝ 日別構成比。
  Excel: ='01'!D2 / '01'!$NE2（NE=期間合計＝年間SUM）。
-#}
{{ config(materialized='table') }}

select
    facility_code,
    facility_name,
    event_date,
    sense_value,
    div0(sense_value, sum(sense_value) over (partition by facility_code)) as daily_ratio
from {{ ref('s1_int_sense_daily') }}
