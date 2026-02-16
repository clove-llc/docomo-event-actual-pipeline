import pandas as pd


def normalize_daily_result(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()

    s = s.replace({"": pd.NA, "nan": pd.NA})

    s = s.replace(
        {
            "＠": pd.NA,
            "@": pd.NA,
            "中止": pd.NA,
            "確認中": pd.NA,
            "なし": 0,
        }
    )

    return pd.to_numeric(s, errors="coerce").astype("Int64")