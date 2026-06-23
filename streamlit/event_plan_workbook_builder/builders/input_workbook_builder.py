from __future__ import annotations
from io import BytesIO

from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.workbook.workbook import Workbook

from entities import (
    ConstraintDetail,
    DateDetail,
    FacilityDailyTargetDetail,
    FacilityDetail,
)


class InputWorkbookBuilder:
    CONSTRAINT_SHEET_NAME = "制約条件"

    FACILITY_CONDITION_SHEET_NAME = "施設別制約条件"
    FACILITY_CONDITION_START_ROW = 3

    FACILITY_DAILY_TARGET_SHEET_NAME = "施設別・日別_目標値"
    FACILITY_DAILY_TARGET_START_ROW = 3

    DATE_SHEET_NAME = "日付情報"
    DATE_START_ROW = 3

    OUTPUT_SHEET_NAME = "アウトプットデータ形式"
    OUTPUT_START_COL = 3

    def __init__(
        self,
        *,
        wb: Workbook,
        constraint_detail: ConstraintDetail,
        facility_details: list[FacilityDetail],
        date_details: list[DateDetail],
        facility_daily_target_details: list[FacilityDailyTargetDetail],
        input_data_cpa: int | None,
    ) -> None:
        self.wb = wb
        self.constraint_detail = constraint_detail
        self.facility_details = facility_details
        self.date_details = date_details
        self.facility_daily_target_details = facility_daily_target_details
        self.input_data_cpa = input_data_cpa

    def _write_constraint_sheet(
        self,
        ws: Worksheet,
    ) -> None:

        ws[f"C3"] = self.constraint_detail.proposal_period
        ws[f"C4"] = self.constraint_detail.monthly_event_count
        ws[f"C5"] = self.constraint_detail.weekday_pattern
        ws[f"C6"] = self.constraint_detail.target_pi
        ws[f"C7"] = self.constraint_detail.condition_cost
        ws[f"C8"] = self.constraint_detail.target_cpa()
        ws[f"C9"] = self.input_data_cpa

    def _write_facility_condition_sheet(self, ws: Worksheet) -> None:
        for (
            row_offset,
            facility_detail,
        ) in enumerate(self.facility_details):
            row_idx = self.FACILITY_CONDITION_START_ROW + row_offset

            ws[f"B{row_idx}"] = facility_detail.facility_code
            ws[f"C{row_idx}"] = facility_detail.facility_name
            ws[f"D{row_idx}"] = facility_detail.cpa
            ws[f"E{row_idx}"] = facility_detail.is_excluded
            ws[f"F{row_idx}"] = facility_detail.monthly_event_limit
            ws[f"G{row_idx}"] = facility_detail.operating_days

    def _write_facility_daily_target_sheet(self, ws: Worksheet) -> None:
        for row_offset, facility_daily_target_detail in enumerate(
            self.facility_daily_target_details
        ):
            row_idx = self.FACILITY_DAILY_TARGET_START_ROW + row_offset

            ws[f"B{row_idx}"] = facility_daily_target_detail.facility_code
            ws[f"C{row_idx}"] = facility_daily_target_detail.facility_name
            ws[f"D{row_idx}"] = facility_daily_target_detail.po_level
            ws[f"E{row_idx}"] = facility_daily_target_detail.regional_office
            ws[f"F{row_idx}"] = facility_daily_target_detail.branch_office
            ws[f"G{row_idx}"] = facility_daily_target_detail.date
            ws[f"H{row_idx}"] = facility_daily_target_detail.date_flag
            ws[f"I{row_idx}"] = facility_daily_target_detail.target_value

    def _write_date_sheet(self, ws: Worksheet) -> None:
        for row_offset, date_detail in enumerate(self.date_details):
            row_idx = self.DATE_START_ROW + row_offset

            ws[f"B{row_idx}"] = date_detail.date
            ws[f"C{row_idx}"] = date_detail.weekday_name_and_week_number_monthly
            ws[f"D{row_idx}"] = date_detail.date_flag

    def _write_output_sheet_date_header(self, ws: Worksheet) -> None:
        for col_offset, date_detail in enumerate(self.date_details):
            col_idx = self.OUTPUT_START_COL + col_offset

            ws.cell(row=3, column=col_idx, value=date_detail.date)
            ws.cell(
                row=4,
                column=col_idx,
                value=date_detail.weekday_name_and_week_number_monthly,
            )
            ws.cell(row=5, column=col_idx, value=date_detail.date_flag)

    def build(self) -> bytes:
        self._write_constraint_sheet(self.wb[self.CONSTRAINT_SHEET_NAME])
        self._write_facility_condition_sheet(
            self.wb[self.FACILITY_CONDITION_SHEET_NAME]
        )
        self._write_facility_daily_target_sheet(
            self.wb[self.FACILITY_DAILY_TARGET_SHEET_NAME]
        )
        self._write_date_sheet(self.wb[self.DATE_SHEET_NAME])
        self._write_output_sheet_date_header(self.wb[self.OUTPUT_SHEET_NAME])

        output = BytesIO()
        self.wb.save(output)
        output.seek(0)

        return output.getvalue()
