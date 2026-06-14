{#-
  dynamic_table 検証: 上流（base）モデル。源泉は seed（dyn_source）。
  ※ INCREMENTAL リフレッシュを成立させるため、クエリは「決定的」にする
     （current_timestamp() 等の非決定的関数を入れない）。
  「いつ更新されたか」は、テーブル内のカラムではなく dynamic table のメタデータ
   （SHOW DYNAMIC TABLES の data_timestamp / INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY）で取得する。
-#}
select
    id,
    name
from {{ ref('dyn_source') }}
