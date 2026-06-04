{#-
  横持ち RAW_FACILITY_ACTUALS_<yyyymm> 1テーブルを縦持ち（13列）にする SELECT を返すマクロ。
  UNION ALL で連結できるよう、CTEではなく派生テーブルで構成した単一SELECTを返す。

  前提: 横持ちの日付列は VARCHAR で原文保持（＠/中止/なし/不明/空/数値）。
  縦持ち化後の「日付実績」をテーブル定義書の仕様でクレンジングする:
    - 空セル（完全未入力）→ 行削除 / TRIM
    - ＠ / @ / 中止 / 確認中 → NULL（行は残す）
    - なし → 0 / カンマ除去のうえ数値（Int64）
    - 不明 等その他文字 → 行削除

  引数:
    relation          : 対象の横持ちテーブル（Relation）
    source_sheet_name : 出力する source_sheet_name（例: '202504'）
-#}
{% macro unpivot_facility_actuals(relation, source_sheet_name) %}
select
    '{{ source_sheet_name }}'                                  as source_sheet_name,
    flat."支社名"                                             as regional_office_name,
    flat."支店"                                               as branch_office_name,
    flat."施設名"                                             as facility_name,
    flat."フロア"                                             as floor_label,
    flat."スペース名"                                         as space_name,
    flat."面積"                                               as area_raw,
    flat."ヘルパー会社"                                       as helper_company_name,
    flat."スタッフ数"                                         as staff_count_raw,
    flat."開始日"                                             as start_date,
    flat."終了日"                                             as end_date,
    to_date(flat.k)                                           as event_date,
    case
        when flat.raw in ('＠', '@', '中止', '確認中') then null   -- ステータス → NULL（行は残す）
        when flat.raw = 'なし' then 0                              -- 実績ゼロ
        else round(try_to_decimal(replace(flat.raw, ',', ''), 38, 4))
    end::number(38,0)                                         as actual_value
from (
    select src.*, f.key as k, trim(f.value::string) as raw
    from (select t.*, object_construct(*) as obj from {{ relation }} t) src,
         lateral flatten(input => src.obj) f
    where f.key rlike '[0-9]{4}-[0-9]{2}-[0-9]{2}'   -- 日付列だけ（固定列・latest_updated_atは除外）
      and src."施設名" is not null                    -- 施設名が空の行は対象外
) flat
where flat.raw <> ''                                  -- 空セルは除外（完全未入力）
  and ( flat.raw in ('＠', '@', '中止', '確認中', 'なし')
        or try_to_decimal(replace(flat.raw, ',', ''), 38, 4) is not null )  -- 不明/その他は除外
{% endmacro %}
