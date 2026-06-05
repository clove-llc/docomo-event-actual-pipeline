{#-
  raw/stg/int/mart の4層をスキーマ名そのままにマッピングする。
  +schema 未指定 → target.schema。指定時 → その名前（大文字）をスキーマ名に。
  例: +schema: stg → STG, +schema: int → INT, +schema: mart → MART
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim | upper }}
  {%- endif -%}
{%- endmacro %}
