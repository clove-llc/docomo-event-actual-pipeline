from datetime import date
from dataclasses import dataclass


@dataclass(frozen=True)
class ConstraintDetail:
    proposal_period: str
    monthly_event_count: int | None
    weekday_pattern: str
    target_pi: int | None
    condition_cost: int | None

    def target_cpa(self) -> int:
        if self.condition_cost is None or self.target_pi is None:
            return 0

        return round(self.condition_cost / self.target_pi)


@dataclass(frozen=True)
class FacilityDetail:
    facility_code: int
    facility_name: str
    po_level: str
    regional_office: str
    branch_office: str | None
    cpa: int | None
    is_excluded: bool | None
    monthly_event_limit: int | None
    available_weekdays: str | None


@dataclass(frozen=True)
class DateDetail:
    date: date
    weekday_name_and_week_number_monthly: str
    date_flag: str


@dataclass(frozen=True)
class FacilityDailyTargetDetail:
    facility_code: int
    facility_name: str
    po_level: str
    regional_office: str
    branch_office: str | None
    cpa: int | None
    is_excluded: bool | None
    date: date
    date_flag: str
    target_value: int

    def search_key(self) -> str:
        return self.facility_name + str(self.date)
