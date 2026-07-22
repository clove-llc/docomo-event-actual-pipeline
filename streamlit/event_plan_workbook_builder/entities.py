from datetime import date
from dataclasses import dataclass


@dataclass(frozen=True)
class ConstraintDetail:
    regional_office: str
    proposal_period: str
    daily_event_limit: int
    weekday_pattern: str
    target_actual: int
    constraint_cost: int

    def target_cpa(self) -> int:
        if self.constraint_cost is None or self.target_actual is None:
            return 0

        return round(self.constraint_cost / self.target_actual)


@dataclass(frozen=True)
class RegionalOfficeScheduleConstraint:
    regional_office: str
    daily_event_limit: int
    operating_days: str


@dataclass(frozen=True)
class FacilityDetail:
    facility_code: int
    facility_name: str
    po_level: str
    regional_office: str
    branch_office: str | None
    cpa: int | None
    monthly_event_limit: str | None
    operating_days: str | None
    avg_weekday_standard_target_seasonal: int | None
    avg_regular_weekend_standard_target_seasonal: int | None
    avg_three_day_holiday_standard_target_seasonal: int | None
    avg_bridge_holiday_standard_target_seasonal: int | None
    avg_gw_standard_target_seasonal: int | None
    avg_obon_standard_target_seasonal: int | None
    avg_new_year_standard_target_seasonal: int | None
    avg_year_end_standard_target_seasonal: int | None
    avg_black_friday_standard_target_seasonal: int | None


@dataclass(frozen=True)
class FacilityDailyTargetDetail:
    facility_code: int
    facility_name: str
    po_level: str
    regional_office: str
    branch_office: str | None
    cpa: int | None
    date: date
    date_flag: str
    target_value: int

    def search_key(self) -> str:
        return self.facility_name + str(self.date)


@dataclass(frozen=True)
class DateDetail:
    date: date
    weekday_name_and_week_number_monthly: str
    date_flag: str


@dataclass(frozen=True)
class RegionalOfficeMonthlyConstraint:
    regional_office: str
    target_actual: int
    constraint_cost: int
    daily_event_limit: int
    weekday_pattern: str
