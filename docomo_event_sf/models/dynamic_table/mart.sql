{#-
  dynamic_table 検証: 下流（mart）モデル。上流 dynamic table base を参照（dynamic table on dynamic table）。
  ※ 下流も INCREMENTAL を維持するため決定的クエリにする。
     （上流が FULL だと下流も FULL に強制される＝FULL は下流へ伝播する）
  更新時刻はメタデータ（data_timestamp / DYNAMIC_TABLE_REFRESH_HISTORY）で確認する。
-#}
select
    id,
    name
from {{ ref('base') }}
