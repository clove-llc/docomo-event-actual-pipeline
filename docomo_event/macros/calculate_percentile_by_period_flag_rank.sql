{% macro
    calculate_percentile_by_period_flag_rank(value_column, percentile, relation_alias)
-%}
    ROUND(
        PERCENTILE_CONT(CAST({{ value_column }} AS FLOAT64), {{ percentile }}) OVER (
            PARTITION BY
                {{ relation_alias }}.benchmark_period_key,
                {{ relation_alias }}.date_flag,
                {{ relation_alias }}.decile_rank
        )
    )
{%- endmacro %}
