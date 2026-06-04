"""Excel → DataFrame の抽出（Streamlit 非依存・純粋関数）。値はすべて str/None。"""

from __future__ import annotations

import pandas as pd


def wide_extract(xls: pd.ExcelFile, sheet: str, header_row: int, first_col: int,
                 fixed_n: int, key_col: str | None):
    """横持ち（固定 fixed_n 列 ＋ 日付列）を取り出す。日付列名は ISO 文字列。"""
    header = pd.read_excel(xls, sheet_name=sheet, header=None,
                           nrows=header_row + 1, engine="openpyxl").iloc[header_row]
    data = pd.read_excel(xls, sheet_name=sheet, header=None,
                         skiprows=header_row + 1, dtype=str, engine="openpyxl")
    header = header.iloc[first_col:].reset_index(drop=True)
    data = data.iloc[:, first_col:].reset_index(drop=True)

    fixed = [str(header.iloc[i]).strip() for i in range(fixed_n)]
    date_names, date_idx = [], []
    for j in range(fixed_n, len(header)):
        d = pd.to_datetime(header.iloc[j], errors="coerce")
        if pd.notna(d):
            date_names.append(d.strftime("%Y-%m-%d"))
            date_idx.append(j)

    data = data.iloc[:, list(range(fixed_n)) + date_idx]
    data.columns = fixed + date_names
    if key_col and key_col in data.columns:
        data = data[data[key_col].notna() & (data[key_col].astype(str).str.strip() != "")]
    data = data.where(pd.notna(data), None).reset_index(drop=True)
    return fixed, date_names, data


def flat_extract(xls: pd.ExcelFile, sheet: str, header_row: int,
                 key_col: str | None) -> pd.DataFrame:
    """フラットな表を取り出す（header_row を列名として使用）。"""
    df = pd.read_excel(xls, sheet_name=sheet, header=header_row, dtype=str, engine="openpyxl")
    keep = [c for c in df.columns
            if not str(c).startswith("Unnamed") and str(c).strip().lower() != "nan"]
    df = df.loc[:, keep]
    df.columns = [str(c).strip() for c in df.columns]
    if key_col and key_col in df.columns:
        df = df[df[key_col].notna() & (df[key_col].astype(str).str.strip() != "")]
    return df.where(pd.notna(df), None).reset_index(drop=True)
