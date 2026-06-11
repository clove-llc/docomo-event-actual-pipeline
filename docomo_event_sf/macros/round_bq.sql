{#-
  BigQuery 互換の ROUND。
  Snowflake の ROUND(x, n) は float リテラル/値を「意図した10進」とみなして丸める（0.95→1.0）が、
  BigQuery の ROUND は IEEE double の実値（0.95→0.94999…）を ties-away で丸める（0.95→0.9）。
  number(38,18) へ cast すると double の実値が保持されるため、それを round すると BigQuery と一致する。

  例:
    round_bq(0.95, 1) = 0.9   （BQ と一致。素の round(0.95,1) は SF だと 1.0）
    round_bq(7.5, 0)  = 8
  注意: FLOAT 集計（AVG 等）の合計順序差により、平均が .x5 境界ちょうどの群はエンジン間で
        最終ビットが異なり、丸め後に ±1 単位ズレる場合がある（原理的に解消不可の残差）。
-#}
{% macro round_bq(col, n=0) -%}
round(cast(({{ col }}) as number(38, 18)), {{ n }})
{%- endmacro %}
