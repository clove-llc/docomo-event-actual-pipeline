from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import streamlit as st

from config import PAGE_TITLE, REGIONAL_OFFICE_NAMES
from excel_builder import build_input_excel
from snowflake_repository import (
    fetch_benchmark_period_keys,
    fetch_date_master,
    fetch_facility_targets,
)
from utils import calculate_cpa, format_period, parse_int


@dataclass(frozen=True)
class PlanningSettings:
    regional_office_name: str
    benchmark_period_key: str
    year: int
    month: int

    @property
    def proposal_period(self) -> str:
        return format_period(self.year, self.month)


@dataclass(frozen=True)
class ConstraintValues:
    monthly_event_count: int | None
    weekday_pattern: str
    target_pi: int | None
    condition_cost: int | None
    errors: list[str]


def validate_constraint_inputs(
    *,
    monthly_event_count_text: str,
    monthly_event_count: int | None,
    target_pi_text: str,
    target_pi: int | None,
    condition_cost_text: str,
    condition_cost: int | None,
) -> list[str]:
    errors: list[str] = []

    if monthly_event_count_text.strip() != "" and monthly_event_count is None:
        errors.append("稼働ラインは整数で入力してください。")

    if target_pi_text.strip() != "" and target_pi is None:
        errors.append("目標実績は整数で入力してください。")

    if condition_cost_text.strip() != "" and condition_cost is None:
        errors.append("条件コストは整数で入力してください。")

    if target_pi == 0:
        errors.append("目標実績が0のため、CPAを計算できません。")

    # condition_cost は空欄を許容するので、現時点では参照だけで十分。
    _ = condition_cost

    return errors


def load_facility_targets(settings: PlanningSettings) -> pd.DataFrame:
    st.subheader("施設別の目標値を取得")

    try:
        facility_targets_raw_df = fetch_facility_targets(
            settings.benchmark_period_key,
            settings.year,
            settings.month,
            settings.regional_office_name,
        )
    except Exception as exc:  # noqa: BLE001
        st.error("Snowflakeから施設別目標値を取得できませんでした。")
        st.exception(exc)
        st.stop()

    st.write(
        f"Snowflakeから「{settings.regional_office_name}」の目標値を "
        f"{len(facility_targets_raw_df):,} 件取得しました。"
    )
    render_dataframe_preview("取得した目標値を確認する", facility_targets_raw_df)

    return facility_targets_raw_df


def load_date_master(settings: PlanningSettings) -> pd.DataFrame:
    st.subheader("日付情報を取得")

    try:
        date_master_df = fetch_date_master(year=settings.year, month=settings.month)
    except Exception as exc:  # noqa: BLE001
        st.error("Snowflakeから日付情報を取得できませんでした。")
        st.exception(exc)
        st.stop()

    st.write(
        f"Snowflakeから「{settings.year}/{settings.month}」の日付情報を "
        f"{len(date_master_df):,} 件取得しました。"
    )
    render_dataframe_preview("取得した日付情報を確認する", date_master_df)

    return date_master_df


def render_settings_section() -> PlanningSettings:
    st.subheader("計画値設定")

    col_regional_office, col_benchmark_period_keys = st.columns(2)

    try:
        benchmark_period_keys = fetch_benchmark_period_keys()
    except Exception as exc:  # noqa: BLE001
        st.error("Snowflakeから過去実績対象期間を取得できませんでした。")
        st.exception(exc)
        st.stop()

    if not benchmark_period_keys:
        st.error("過去実績対象期間が取得できませんでした。")
        st.stop()

    with col_benchmark_period_keys:
        selected_benchmark_period_key = str(
            st.selectbox(
                "過去実績対象期間",
                benchmark_period_keys,
                index=0,
            )
        )

    with col_regional_office:
        selected_regional_office = str(
            st.selectbox(
                "支社",
                REGIONAL_OFFICE_NAMES,
                index=0,
            )
        )

    col_year, col_month = st.columns(2)
    current_year = datetime.now().year
    current_month = datetime.now().month

    with col_year:
        selected_year = int(
            st.selectbox(
                "対象年度",
                options=list(range(current_year, current_year + 3)),
                index=0,
            )
        )

    with col_month:
        selected_month = int(
            st.selectbox(
                "対象月",
                options=list(range(1, 13)),
                index=current_month - 1,
            )
        )

    return PlanningSettings(
        regional_office_name=selected_regional_office,
        benchmark_period_key=selected_benchmark_period_key,
        year=selected_year,
        month=selected_month,
    )


def render_constraint_section(proposal_period: str) -> ConstraintValues:
    st.subheader("制約条件")

    col_proposal_period, col_monthly_event_count, col_weekday_pattern = st.columns(3)

    with col_proposal_period:
        st.text_input(
            "提案期間",
            value=proposal_period,
            disabled=True,
        )

    with col_monthly_event_count:
        monthly_event_count_text = st.text_input(
            "稼働ライン",
            value="",
            placeholder="例: 113",
        )

    with col_weekday_pattern:
        weekday_pattern = st.text_input(
            "稼働曜日",
            value="",
            placeholder="例: 金～日",
        )

    col_target_pi, col_condition_cost, col_target_cpt = st.columns(3)

    with col_target_pi:
        target_pi_text = st.text_input(
            "目標実績（PI）",
            value="",
            placeholder="例: 5,595",
        )

    with col_condition_cost:
        condition_cost_text = st.text_input(
            "条件コスト（円）",
            value="",
            placeholder="例: 247,543,639",
        )

    monthly_event_count = parse_int(monthly_event_count_text)
    target_pi = parse_int(target_pi_text)
    condition_cost = parse_int(condition_cost_text)
    target_cpa = calculate_cpa(condition_cost, target_pi)

    with col_target_cpt:
        st.text_input(
            "目標CPA水準（円）",
            value="" if target_cpa is None else f"{target_cpa:,}",
            placeholder="※ 条件コスト/目標実績 の結果",
            disabled=True,
        )

    errors = validate_constraint_inputs(
        monthly_event_count_text=monthly_event_count_text,
        monthly_event_count=monthly_event_count,
        target_pi_text=target_pi_text,
        target_pi=target_pi,
        condition_cost_text=condition_cost_text,
        condition_cost=condition_cost,
    )

    for error in errors:
        st.error(error)

    return ConstraintValues(
        monthly_event_count=monthly_event_count,
        weekday_pattern=weekday_pattern,
        target_pi=target_pi,
        condition_cost=condition_cost,
        errors=errors,
    )


def render_dataframe_preview(title: str, df: pd.DataFrame) -> None:
    with st.expander(title):
        st.dataframe(df, hide_index=True, width="stretch")


def render_download_button(
    *,
    settings: PlanningSettings,
    constraints: ConstraintValues,
    date_master_df: pd.DataFrame,
    facility_targets_raw_df: pd.DataFrame,
) -> None:
    excel_bytes = build_input_excel(
        proposal_period=settings.proposal_period,
        monthly_event_count=constraints.monthly_event_count,
        weekday_pattern=constraints.weekday_pattern,
        target_pi=constraints.target_pi,
        condition_cost=constraints.condition_cost,
        date_master_df=date_master_df,
        facility_targets_raw_df=facility_targets_raw_df,
    )

    file_name = (
        f"{settings.regional_office_name}_AI入力シート_"
        f"{settings.year}{settings.month:02d}.xlsx"
    )

    st.download_button(
        label="Excelをダウンロード",
        data=excel_bytes,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        disabled=len(constraints.errors) > 0 or len(facility_targets_raw_df) == 0,
    )


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(PAGE_TITLE)

    st.divider()
    settings = render_settings_section()

    st.divider()
    constraints = render_constraint_section(settings.proposal_period)

    st.divider()
    facility_targets_raw_df = load_facility_targets(settings)

    st.divider()
    date_master_df = load_date_master(settings)

    render_download_button(
        settings=settings,
        constraints=constraints,
        date_master_df=date_master_df,
        facility_targets_raw_df=facility_targets_raw_df,
    )


if __name__ == "__main__":
    main()
