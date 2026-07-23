from __future__ import annotations
import calendar

import pandas as pd
import streamlit as st

from typing import cast
from datetime import datetime
from dataclasses import asdict, dataclass

from config import (
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


@dataclass(frozen=True)
class PlanningSetting:
    benchmark_period_key: str
    year: int
    month: int
    proposal_period: str

    def get_period_prefix(self) -> str:
        return f"{self.year}年{self.month}月_"


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
            value=f"{selected_year}/{selected_month}/1~{selected_year}/{selected_month}/{calendar.monthrange(selected_year, selected_month)[1]}",
            disabled=True,
        )

    return PlanningSetting(
        benchmark_period_key=selected_benchmark_period_key,
        year=selected_year,
        month=selected_month,
        proposal_period=selected_proposal_period,
    )


def render_constraint_section(
    planning_settings: PlanningSetting,
    regional_office_monthly_constraints: list[RegionalOfficeMonthlyConstraint],
) -> list[ConstraintDetail]:
    st.subheader("制約条件")

    if not regional_office_monthly_constraints:
        st.warning("対象期間の制約条件がありません。")
        return []

    constraint_df = pd.DataFrame(
        [asdict(constraint) for constraint in regional_office_monthly_constraints]
    )

    # 対象期間が変わった場合は別のdata_editorとして扱う
    editor_key = f"constraint_editor_" f"{planning_settings.proposal_period}"
    form_key = f"constraint_form_" f"{planning_settings.proposal_period}"

    with st.form(form_key):
        edited_df = st.data_editor(
            constraint_df,
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
            daily_event_limit=int(cast(int, row.daily_event_limit)),
            weekday_pattern=str(row.operating_days),
            target_actual=int(cast(int, row.target_actual)),
            constraint_cost=int(cast(int, row.constraint_cost)),
        )
        for row in edited_df.itertuples(index=False)
    ]

    return constraint_details


def render_dataframe_preview(
    title: str,
    df: pd.DataFrame,
) -> None:
    st.subheader(title)

    st.write(f"Snowflakeから{title}を " f"{len(df):,} 件取得しました。")

    with st.expander(title):
        st.dataframe(df, hide_index=True, width="stretch")


def render_download_button(
    *,
    planning_setting: PlanningSetting,
    constraint_details: list[ConstraintDetail],
    facility_details: list[FacilityDetail],
    cpa_avg: int,
    facility_daily_target_details: list[FacilityDailyTargetDetail],
    date_details: list[DateDetail],
) -> None:
    disabled = (
        len(constraint_details) == 0
        or len(facility_details) == 0
        or len(facility_daily_target_details) == 0
        or len(date_details) == 0
    )

    st.subheader("Excelファイル生成 / ダウンロード")

    if disabled:
        st.warning("Excelファイルの生成に必要なデータが不足しています。")
        return

    input_workbook_bytes: bytes | None = None
    output_workbook_bytes: bytes | None = None

    if st.button("設定した情報でExcelファイルを生成する", type="primary"):
        try:
            with st.spinner("Excelファイルを生成中です..."):
                input_workbook_bytes = InputWorkbookBuilder(
                    constraint_details=constraint_details,
                    facility_details=facility_details,
                    cpa_avg=cpa_avg,
                    date_details=date_details,
                    facility_daily_target_details=facility_daily_target_details,
                ).build()

                output_workbook_bytes = OutputWorkbookBuilder(
                    constraint_details=constraint_details,
                    facility_details=facility_details,
                    cpa_avg=cpa_avg,
                    date_details=date_details,
                    facility_daily_target_details=facility_daily_target_details,
                ).build()

            st.success("Excelファイルの生成が完了しました。")
        except Exception as e:
            st.error(f"Excelファイル生成中にエラーが発生しました: {e}")

    col_input, col_output = st.columns(2)

    if input_workbook_bytes:
        with col_input:
            st.download_button(
                label="入力シート一式をダウンロード",
                data=input_workbook_bytes,
                file_name=f"{planning_setting.get_period_prefix()}Copilot入力用Excel.zip",
                mime="application/zip",
                type="primary",
                on_click="ignore",
            )

    if output_workbook_bytes:
        with col_output:
            st.download_button(
                label="出力シート一式をダウンロード",
                data=output_workbook_bytes,
                file_name=f"{planning_setting.get_period_prefix()}Copilot出力用Excel.zip",
                mime="application/zip",
                type="primary",
                on_click="ignore",
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
    facility_details, cpa_avg = fetch_facility_details(
        planning_setting.benchmark_period_key,
        planning_setting.year,
        planning_setting.month,
    )
    render_dataframe_preview(
        "施設情報",
        pd.DataFrame([asdict(detail) for detail in facility_details]),
    )

    st.divider()
    facility_daily_target_details = fetch_facility_daily_target_details(
        planning_setting.benchmark_period_key,
        planning_setting.year,
        planning_setting.month,
    )
    render_dataframe_preview(
        "施設別・日別目標値",
        pd.DataFrame([asdict(detail) for detail in facility_daily_target_details]),
    )

    st.divider()
    date_details = fetch_date_master(
        year=planning_setting.year, month=planning_setting.month
    )
    render_dataframe_preview(
        "日付情報",
        pd.DataFrame([asdict(detail) for detail in date_details]),
    )

    render_download_button(
        planning_setting=planning_setting,
        constraint_details=constraint_details,
        facility_details=facility_details,
        cpa_avg=cpa_avg,
        facility_daily_target_details=facility_daily_target_details,
        date_details=date_details,
    )


if __name__ == "__main__":
    main()
