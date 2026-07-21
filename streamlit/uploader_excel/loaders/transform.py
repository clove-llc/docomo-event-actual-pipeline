"""型変換とDDL生成（Streamlit 非依存・純粋関数）。すべて列の SQL 型で駆動する。"""

from __future__ import annotations

from typing import Callable

import pandas as pd

AUDIT_COL = "latest_updated_at"


def to_bool(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    t = str(v).strip().lower()
    if t in ("true", "1", "1.0"):
        return True
    if t in ("false", "0", "0.0"):
        return False
    return None


def _to_number(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.map(lambda v: None if v is None else str(v).replace(",", "").replace("，", "")),
        errors="coerce")


def _to_date_str(s: pd.Series) -> pd.Series:
    """YYYY-MM-DD 文字列に（datetime64のまま渡すと Snowflake で variant→DATE 変換に失敗）。"""
    d = pd.to_datetime(s, errors="coerce")
    return d.dt.strftime("%Y-%m-%d").where(d.notna(), None)


def cast_by_type(df: pd.DataFrame, type_for: Callable[[str], str]) -> pd.DataFrame:
    """各列を SQL 型に合わせて変換。DATE=日付文字列 / NUMBER=数値 / BOOLEAN=真偽 / それ以外=原文。"""
    out = df.copy()
    for c in out.columns:
        t = type_for(c).upper()
        if t.startswith("DATE"):
            out[c] = _to_date_str(out[c])
        elif t.startswith("NUMBER") or t in ("INT", "INTEGER", "FLOAT"):
            out[c] = _to_number(out[c])
        elif t.startswith("BOOL"):
            out[c] = out[c].map(to_bool)
        else:  # VARCHAR など：原文のまま（NaN→None）
            out[c] = out[c].where(pd.notna(out[c]), None)
    return out


def build_ddl(fqtn: str, columns: list[str], type_for: Callable[[str], str]) -> str:
    cols = [f'  "{c}" {type_for(c)}' for c in columns]
    cols.append(f'  "{AUDIT_COL}" TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()')
    return f"CREATE OR REPLACE TABLE {fqtn} (\n" + ",\n".join(cols) + "\n)"
