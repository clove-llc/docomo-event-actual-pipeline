{% macro
    calculate_percentile_by_period_flag_rank(value_column, percentile, relation_alias)
-%}
    CAST(ROUND(
        PERCENTILE_CONT({{ value_column }}, {{ percentile }}) OVER (
            PARTITION BY
                {{ relation_alias }}.benchmark_period_key,
                {{ relation_alias }}.date_flag,
                {{ relation_alias }}.decile_rank
        )
    ) AS INT64)
{%- endmacro %}
