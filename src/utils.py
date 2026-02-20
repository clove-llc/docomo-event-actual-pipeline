from pathlib import Path

import pandas as pd


def load_sql(file_name: str) -> str:
    sql_path = Path(__file__).parent / "sql" / file_name
    return sql_path.read_text(encoding="utf-8")


def to_string(series: pd.Series) -> pd.Series:
    return series.astype("string")


def to_integer(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
        .floordiv(1)
        .astype("Int64")
    )


def to_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def to_boolean(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map(
            {
                "true": True,
                "false": False,
                "1": True,
                "0": False,
                "yes": True,
                "no": False,
                "○": True,
                "×": False,
                "": pd.NA,
            }
        )
        .astype("boolean")
    )
