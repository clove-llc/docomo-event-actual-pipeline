{#-
  カスタムスキーマ指定時は target.schema_<suffix> に出力する（既存 docomo_event と同方針）。
  例: target.schema=STREAMLIT_UPLODER_XLSX, +schema: int → STREAMLIT_UPLODER_XLSX_INT
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ target.schema }}_{{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
