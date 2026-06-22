from __future__ import annotations

import datetime
import calendar

from datetime import date
from typing import Any

from entities import FacilityDetail


def to_date(value: Any) -> date:
    if isinstance(value, datetime.datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value)[:10])


def parse_int(value: str) -> int | None:
    """カンマ付き数値文字列を int に変換する。空欄は None。"""
    normalized = value.replace(",", "").strip()

    if normalized == "":
        return None

    try:
        return int(normalized)
    except ValueError:
        return None


def format_period(year: int, month: int) -> str:
    """対象年月から提案期間文字列を作成する。"""
    last_day = calendar.monthrange(year, month)[1]
    return f"{year}/{month}/1~{year}/{month}/{last_day}"


def calculate_cpa(condition_cost: int | None, target_pi: int | None) -> int | None:
    """条件コスト / 目標PI からCPAを計算する。"""
    if condition_cost is None or target_pi is None or target_pi == 0:
        return None

    return round(condition_cost / target_pi)


def calculate_input_data_cpa(
    facility_details: list[FacilityDetail],
) -> int | None:
    cpa_values = [detail.cpa for detail in facility_details if detail.cpa is not None]

    if len(cpa_values) == 0:
        return None

    return round(sum(cpa_values) / len(cpa_values))
