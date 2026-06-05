{#-
  RAW_FACILITY_ACTUALS_<yyyymm>（横持ち・月別）を全月まとめて縦持ち化するモデル。

  - dbt_utils.get_relations_by_pattern で RAW_FACILITY_ACTUALS_2xxxxx を自動検出。
  - for で各月テーブルを unpivot_facility_actuals マクロに通し、UNION ALL するだけ。
  - 月テーブルが増えても、このモデルは無変更で自動対応する。
  - source_sheet_name は テーブル名末尾6桁（例: 202504）。

  前提: dbt_utils（packages.yml）／ Snowflakeターゲット／ 横持ち日付列はVARCHAR原文。
  別DB/スキーマにある場合は database= / schema_pattern= を明示する（var化推奨）。
-#}

{{ config(materialized='table') }}

{%- set relations = dbt_utils.get_relations_by_pattern(
      schema_pattern=target.schema,
      table_pattern='RAW_FACILITY_ACTUALS_2%'
) -%}

{%- if relations | length == 0 -%}
  {{ exceptions.raise_compiler_error("RAW_FACILITY_ACTUALS_<yyyymm> テーブルが見つかりません: " ~ target.schema) }}
{%- endif -%}

{%- for rel in relations %}
{{ unpivot_facility_actuals(rel, rel.identifier[-6:]) }}
{%- if not loop.last %}
union all
{% endif %}
{%- endfor %}
