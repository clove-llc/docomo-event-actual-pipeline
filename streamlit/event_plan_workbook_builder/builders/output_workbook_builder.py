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


class OutputWorkbookBuilder:
    CONSTRAINT_SHEET_NAME = "制約条件"

    COPILOT_OUTPUT_SHEET_NAME = "Copilotの出力結果"

    FACILITY_OUTPUT_SHEET_NAMES = [
        "想定実績値_集計",
        "想定コスト_集計",
        "想定CPA_集計",
        "最適なスタッフ数_集計",
    ]

    FACILITY_OUTPUT_START_ROW = 7

    FACILITY_DAILY_TARGET_SHEET_NAME = "施設別・日別_目標値"

    FACILITY_DAILY_TARGET_START_ROW = 3

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

    def _write_facility_output_sheet(
        self,
        ws: Worksheet,
    ) -> None:
        for (
            row_offset,
            facility_detail,
        ) in enumerate(self.facility_details):
            row_idx = self.FACILITY_OUTPUT_START_ROW + row_offset

            ws[f"B{row_idx}"] = facility_detail.facility_name
            ws[f"C{row_idx}"] = facility_detail.po_level
            ws[f"D{row_idx}"] = facility_detail.regional_office
            ws[f"E{row_idx}"] = facility_detail.branch_office
            ws[f"F{row_idx}"] = facility_detail.cpa
            ws[f"G{row_idx}"] = facility_detail.is_excluded
            ws[f"H{row_idx}"] = facility_detail.monthly_event_limit
            ws[f"I{row_idx}"] = facility_detail.available_weekdays

    def _write_date_header(self, ws: Worksheet, start_col: int = 10) -> None:
        for col_offset, date_detail in enumerate(self.date_details):
            col_idx = start_col + col_offset

            ws.cell(row=4, column=col_idx, value=date_detail.date)
            ws.cell(
                row=5,
                column=col_idx,
                value=date_detail.weekday_name_and_week_number_monthly,
            )
            ws.cell(row=6, column=col_idx, value=date_detail.date_flag)

    def _write_facility_daily_target_sheet(self, ws: Worksheet) -> None:
        for row_offset, facility_daily_target_detail in enumerate(
            self.facility_daily_target_details
        ):
            row_idx = self.FACILITY_DAILY_TARGET_START_ROW + row_offset

            ws[f"B{row_idx}"] = facility_daily_target_detail.search_key()
            ws[f"C{row_idx}"] = facility_daily_target_detail.facility_name
            ws[f"D{row_idx}"] = facility_daily_target_detail.date
            ws[f"E{row_idx}"] = facility_daily_target_detail.date_flag
            ws[f"F{row_idx}"] = facility_daily_target_detail.target_value

    def build(self) -> bytes:
        self._write_constraint_sheet(self.wb[self.CONSTRAINT_SHEET_NAME])

        self._write_facility_output_sheet(self.wb[self.COPILOT_OUTPUT_SHEET_NAME])
        self._write_date_header(self.wb[self.COPILOT_OUTPUT_SHEET_NAME], start_col=18)

        for sheet_name in self.FACILITY_OUTPUT_SHEET_NAMES:
            ws = self.wb[sheet_name]

            self._write_facility_output_sheet(ws)

            self._write_date_header(ws)

        self._write_facility_daily_target_sheet(
            ws=self.wb[self.FACILITY_DAILY_TARGET_SHEET_NAME]
        )

        output = BytesIO()
        self.wb.save(output)
        output.seek(0)

        return output.getvalue()
