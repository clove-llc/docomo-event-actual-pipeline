from __future__ import annotations

import pandas as pd
import streamlit as st

from typing import cast
from datetime import datetime
from dataclasses import asdict, dataclass
from openpyxl import load_workbook
from config import (
    COPILOT_INPUT_TEMPLATE_PATH,
    COPILOT_OUTPUT_TEMPLATE_PATH,
    PAGE_TITLE,
)

from snowflake_repository import (
    fetch_benchmark_period_keys,
    fetch_date_master,
    fetch_facility_daily_target_details,
    fetch_facility_details,
    fetch_monthly_constraints_master,
)
from entities import (
    ConstraintDetail,
    DateDetail,
    FacilityDailyTargetDetail,
    FacilityDetail,
    RegionalOfficeMonthlyConstraint,
)
from builders.input_workbook_builder import (
    InputWorkbookBuilder,
)
from builders.output_workbook_builder import (
    OutputWorkbookBuilder,
)
from utils import format_period

APPLIED_CONNECTION_SETTING_KEY = "applied_connection_setting"


@dataclass(frozen=True)
class PlanningSetting:
    benchmark_period_key: str
    year: int
    month: int
    proposal_period: str

    def get_period_prefix(self) -> str:
        return f"{self.year}年{self.month}月_"


def load_facility_daily_target_details(
    settings: PlanningSetting,
) -> list[FacilityDailyTargetDetail]:
    st.subheader("施設別・日別目標値")

    facility_daily_target_details = fetch_facility_daily_target_details(
        settings.benchmark_period_key,
        settings.year,
        settings.month,
    )

    st.write(
        f"Snowflakeから「{settings.year}/{settings.month}」の目標値を "
        f"{len(facility_daily_target_details):,} 件取得しました。"
    )
    render_dataframe_preview(
        "取得した目標値を確認する",
        pd.DataFrame([asdict(detail) for detail in facility_daily_target_details]),
    )

    return facility_daily_target_details


def load_facility_details(
    settings: PlanningSetting,
) -> list[FacilityDetail]:
    st.subheader("施設情報")

    facility_details = fetch_facility_details(
        settings.benchmark_period_key,
        settings.year,
        settings.month,
    )

    st.write(f"Snowflakeから施設情報を " f"{len(facility_details):,} 件取得しました。")
    render_dataframe_preview(
        "取得した施設情報を確認する",
        pd.DataFrame([asdict(detail) for detail in facility_details]),
    )

    return facility_details


def load_date_details(settings: PlanningSetting) -> list[DateDetail]:
    st.subheader("日付情報")

    date_details = fetch_date_master(year=settings.year, month=settings.month)

    st.write(
        f"Snowflakeから「{settings.year}/{settings.month}」の日付情報を "
        f"{len(date_details):,} 件取得しました。"
    )
    render_dataframe_preview(
        "取得した日付情報を確認する",
        pd.DataFrame([asdict(detail) for detail in date_details]),
    )

    return date_details


def render_planning_settings_section(
    benchmark_period_keys: list[str],
) -> PlanningSetting:
    st.subheader("対象期間")

    col_year, col_month, col_benchmark_period_keys, col_proposal_period = st.columns(
        [1, 1, 2, 2]
    )
    current_year = datetime.now().year
    current_month = datetime.now().month

    with col_year:
        selected_year = int(
            st.selectbox(
                "対象年度",
                options=list(range(current_year, current_year + 3)),
                index=0,
                help="イベントプランを作成したい年度",
            )
        )

    with col_month:
        selected_month = int(
            st.selectbox(
                "対象月",
                options=list(range(1, 13)),
                index=current_month - 1,
                help="イベントプランを作成したい月",
            )
        )

    with col_benchmark_period_keys:
        selected_benchmark_period_key = str(
            st.selectbox(
                "過去実績期間",
                benchmark_period_keys,
                index=0,
                help="目標値を算出する際に対象となる過去実績の期間",
            )
        )

    with col_proposal_period:
        selected_proposal_period = st.text_input(
            "対象期間",
            value=format_period(selected_year, selected_month),
            disabled=True,
        )

    return PlanningSetting(
        benchmark_period_key=selected_benchmark_period_key,
        year=selected_year,
        month=selected_month,
        proposal_period=selected_proposal_period,
    )


def create_constraint_dataframe(
    regional_office_constraints: list[RegionalOfficeMonthlyConstraint],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "regional_office": regional_office_constraint.regional_office,
                "daily_event_limit": regional_office_constraint.daily_event_limit,
                "operating_days": regional_office_constraint.weekday_pattern,
                "target_actual": regional_office_constraint.target_actual,
                "constraint_cost": regional_office_constraint.constraint_cost,
            }
            for regional_office_constraint in regional_office_constraints
        ],
        columns=[
            "regional_office",
            "daily_event_limit",
            "operating_days",
            "target_actual",
            "constraint_cost",
        ],
    )


def render_constraint_section(
    planning_settings: PlanningSetting,
    regional_office_monthly_constraints: list[RegionalOfficeMonthlyConstraint],
) -> list[ConstraintDetail]:
    st.subheader("制約条件")

    if not regional_office_monthly_constraints:
        st.warning("対象期間の制約条件がありません。")
        return []

    constraint_df = create_constraint_dataframe(regional_office_monthly_constraints)

    # 対象期間が変わった場合は別のdata_editorとして扱う
    editor_key = f"constraint_editor_" f"{planning_settings.proposal_period}"
    form_key = f"constraint_form_" f"{planning_settings.proposal_period}"

    with st.form(form_key):
        edited_df = st.data_editor(
            constraint_df,
            column_order=[
                "regional_office",
                "daily_event_limit",
                "operating_days",
                "target_actual",
                "constraint_cost",
            ],
            column_config={
                "regional_office": st.column_config.TextColumn(
                    "支社",
                    width="small",
                    disabled=True,
                ),
                "daily_event_limit": st.column_config.NumberColumn(
                    "日当たり稼働ライン",
                    min_value=0,
                    step=1,
                    required=True,
                ),
                "operating_days": st.column_config.TextColumn(
                    "稼働曜日",
                    width="medium",
                    required=True,
                ),
                "target_actual": st.column_config.NumberColumn(
                    "目標実績（PI）",
                    min_value=0,
                    step=1,
                    required=True,
                ),
                "constraint_cost": st.column_config.NumberColumn(
                    "条件コスト（円）",
                    min_value=0,
                    step=1,
                    required=True,
                ),
            },
            num_rows="fixed",
            hide_index=True,
            width="stretch",
            key=editor_key,
        )

        submitted = st.form_submit_button(
            "変更を反映",
            type="primary",
        )

    if submitted:
        st.success("制約条件を反映しました。")

    constraint_details = [
        ConstraintDetail(
            regional_office=str(row.regional_office),
            proposal_period=planning_settings.proposal_period,
            daily_event_limit=int(cast(int | float, row.daily_event_limit)),
            weekday_pattern=str(row.operating_days),
            target_actual=int(cast(int | float, row.target_actual)),
            constraint_cost=int(cast(int | float, row.constraint_cost)),
        )
        for row in edited_df.itertuples(index=False)
    ]

    return constraint_details


def render_dataframe_preview(title: str, df: pd.DataFrame) -> None:
    with st.expander(title):
        st.dataframe(df, hide_index=True, width="stretch")


def render_download_button(
    *,
    planning_setting: PlanningSetting,
    constraint_details: list[ConstraintDetail],
    facility_details: list[FacilityDetail],
    facility_daily_target_details: list[FacilityDailyTargetDetail],
    date_details: list[DateDetail],
) -> None:
    disabled = (
        len(constraint_details) == 0
        or len(facility_details) == 0
        or len(facility_daily_target_details) == 0
        or len(date_details) == 0
    )

    st.subheader("Excelファイルダウンロード")

    if disabled:
        st.warning("Excelファイルの生成に必要なデータが不足しています。")
        return

    col_input_workbook_download_button, col_output_workbook_download_button = (
        st.columns(2)
    )

    input_workbook_bytes = InputWorkbookBuilder(
        constraint_details=constraint_details,
        facility_details=facility_details,
        date_details=date_details,
        facility_daily_target_details=facility_daily_target_details,
    ).build()
    output_workbook_bytes = OutputWorkbookBuilder(
        constraint_details=constraint_details,
        facility_details=facility_details,
        date_details=date_details,
        facility_daily_target_details=facility_daily_target_details,
    ).build()

    st.info("ボタンを押すとExcelファイルをダウンロードできます。")

    with col_input_workbook_download_button:
        st.download_button(
            label="入力シート一式をダウンロード",
            data=input_workbook_bytes,
            file_name=f"{planning_setting.get_period_prefix()}Copilot入力用Excel.zip",
            mime="application/zip",
            type="primary",
        )

    with col_output_workbook_download_button:
        st.download_button(
            label="出力シート一式をダウンロード",
            data=output_workbook_bytes,
            file_name=f"{planning_setting.get_period_prefix()}Copilot出力用Excel.zip",
            mime="application/zip",
            type="primary",
        )


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(PAGE_TITLE)

    st.divider()
    benchmark_period_keys = fetch_benchmark_period_keys()
    planning_setting = render_planning_settings_section(benchmark_period_keys)

    st.divider()
    regional_office_monthly_constraints = fetch_monthly_constraints_master(
        planning_setting.year, planning_setting.month
    )
    constraint_details = render_constraint_section(
        planning_setting,
        regional_office_monthly_constraints,
    )

    st.divider()
    facility_details = load_facility_details(planning_setting)

    st.divider()
    facility_daily_target_details = load_facility_daily_target_details(
        planning_setting,
    )

    st.divider()
    date_details = load_date_details(planning_setting)

    render_download_button(
        planning_setting=planning_setting,
        constraint_details=constraint_details,
        facility_details=facility_details,
        facility_daily_target_details=facility_daily_target_details,
        date_details=date_details,
    )


if __name__ == "__main__":
    main()
