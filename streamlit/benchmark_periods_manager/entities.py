from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BenchmarkPeriod:
    benchmark_period_key: str
    benchmark_period_name: str
    period_start_date: date
    period_end_date: date
    period_month_count: int
