from __future__ import annotations

import pandas as pd
import streamlit as st

try:
    from common.snowflake_client import fetch_current_database_name, fetch_schema_names
    from common.connection_settings import ConnectionSettings, build_connection_settings
except ModuleNotFoundError:
    from pathlib import Path
    import sys

    streamlit_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(streamlit_root))

    from common.snowflake_client import fetch_current_database_name, fetch_schema_names
    from common.connection_settings import ConnectionSettings, build_connection_settings

from datetime import datetime
from dataclasses import asdict, dataclass
from openpyxl import load_workbook
from config import (
    COPILOT_INPUT_TEMPLATE_PATH,
    COPILOT_OUTPUT_TEMPLATE_PATH,
    EXCEL_MIME_TYPE,
    PAGE_TITLE,
    REGIONAL_OFFICE_NAMES,
)
from snowflake_repository import (
    fetch_benchmark_period_keys,
    fetch_date_master,
    fetch_facility_daily_target_details,
    fetch_facility_details,
    fetch_regional_office_schedule_constraints,
)
from entities import (
    ConstraintDetail,
    DateDetail,
    FacilityDailyTargetDetail,
    FacilityDetail,
    RegionalOfficeScheduleConstraint,
)
from builders.input_workbook_builder import (
    InputWorkbookBuilder,
)
from builders.output_workbook_builder import (
    OutputWorkbookBuilder,
)
from utils import calculate_cpa, calculate_input_data_cpa, format_period, parse_int


@dataclass(frozen=True)
class PlanningSettings:
    regional_office_name: str
    benchmark_period_key: str
    year: int
    month: int

    @property
    def proposal_period(self) -> str:
        return format_period(self.year, self.month)


def validate_constraint_inputs(
    *,
    daily_event_limit_text: str | None,
    daily_event_limit: int | None,
    target_pi_text: str,
    target_pi: int | None,
    condition_cost_text: str,
    condition_cost: int | None,
) -> list[str]:
    errors: list[str] = []

    if not daily_event_limit_text or (
        daily_event_limit_text.strip() != "" and daily_event_limit is None
    ):
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


def load_facility_daily_target_details(
    connection_settings: ConnectionSettings,
    settings: PlanningSettings,
) -> list[FacilityDailyTargetDetail]:
    st.subheader("施設別・日別目標値")

    try:
        facility_daily_target_details = fetch_facility_daily_target_details(
            connection_settings,
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
        f"Snowflakeから「{settings.regional_office_name}」の「{settings.year}/{settings.month}」の目標値を "
        f"{len(facility_daily_target_details):,} 件取得しました。"
    )
    render_dataframe_preview(
        "取得した目標値を確認する",
        pd.DataFrame([asdict(detail) for detail in facility_daily_target_details]),
    )

    return facility_daily_target_details


def load_facility_details(
    connection_settings: ConnectionSettings,
    settings: PlanningSettings,
) -> list[FacilityDetail]:
    st.subheader("対象支社の施設情報")

    try:
        facility_details = fetch_facility_details(
            connection_settings,
            settings.benchmark_period_key,
            settings.year,
            settings.month,
            settings.regional_office_name,
        )
    except Exception as exc:  # noqa: BLE001
        st.error("Snowflakeから対象支社の施設情報を取得できませんでした。")
        st.exception(exc)
        st.stop()

    st.write(
        f"Snowflakeから「{settings.regional_office_name}」の施設情報を "
        f"{len(facility_details):,} 件取得しました。"
    )
    render_dataframe_preview(
        "取得した施設情報を確認する",
        pd.DataFrame([asdict(detail) for detail in facility_details]),
    )

    return facility_details


def load_date_details(
    connection_settings: ConnectionSettings, settings: PlanningSettings
) -> list[DateDetail]:
    st.subheader("日付情報")

    try:
        date_details = fetch_date_master(
            connection_settings, year=settings.year, month=settings.month
        )
    except Exception as exc:  # noqa: BLE001
        st.error("Snowflakeから日付情報を取得できませんでした。")
        st.exception(exc)
        st.stop()

    st.write(
        f"Snowflakeから「{settings.year}/{settings.month}」の日付情報を "
        f"{len(date_details):,} 件取得しました。"
    )
    render_dataframe_preview(
        "取得した日付情報を確認する",
        pd.DataFrame([asdict(detail) for detail in date_details]),
    )

    return date_details


def render_connection_settings_section(
    database_name: str,
    schema_names: list[str],
) -> ConnectionSettings | None:
    current_settings = st.session_state.get("applied_connection_settings")

    connection_settings = build_connection_settings(database_name, schema_names)

    with st.form("connection_settings_form"):
        selected_database_name = st.text_input(
            "データベース名",
            value=current_settings.database_name if current_settings else database_name,
        )

        selected_connection_setting = st.selectbox(
            "スキーマ名",
            connection_settings,
            index=0,
            format_func=lambda connection_setting: connection_setting.label,
        )

        submitted = st.form_submit_button(
            "Snowflakeから読み込み",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        st.session_state["applied_connection_settings"] = selected_connection_setting

    return st.session_state.get("applied_connection_settings")


def render_planning_settings_section(
    benchmark_period_keys: list[str],
) -> PlanningSettings:
    st.subheader("計画値")

    col_regional_office, col_benchmark_period_keys = st.columns(2)

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


def render_constraint_section(
    planning_settings: PlanningSettings,
    regional_office_schedule_constraints: list[RegionalOfficeScheduleConstraint],
) -> ConstraintDetail:
    st.subheader("制約条件")

    selected_constraint = next(
        (
            c
            for c in regional_office_schedule_constraints
            if c.regional_office == planning_settings.regional_office_name
        ),
        None,
    )

    col_proposal_period, col_daily_event_limit, col_weekday_pattern = st.columns(3)

    with col_proposal_period:
        st.text_input(
            "提案期間",
            value=planning_settings.proposal_period,
            disabled=True,
        )

    with col_daily_event_limit:
        daily_event_limit_text = st.text_input(
            "日当たり稼働ライン",
            value=selected_constraint.daily_event_limit if selected_constraint else "",
            placeholder="例: 8",
        )

    with col_weekday_pattern:
        weekday_pattern = st.text_input(
            "稼働曜日",
            value=selected_constraint.operating_days if selected_constraint else "",
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

    daily_event_limit = parse_int(daily_event_limit_text)
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
        daily_event_limit_text=daily_event_limit_text,
        daily_event_limit=daily_event_limit,
        target_pi_text=target_pi_text,
        target_pi=target_pi,
        condition_cost_text=condition_cost_text,
        condition_cost=condition_cost,
    )

    for error in errors:
        st.error(error)

    return ConstraintDetail(
        proposal_period=planning_settings.proposal_period,
        monthly_event_count=daily_event_limit,
        weekday_pattern=weekday_pattern,
        target_pi=target_pi,
        condition_cost=condition_cost,
    )


def render_dataframe_preview(title: str, df: pd.DataFrame) -> None:
    with st.expander(title):
        st.dataframe(df, hide_index=True, width="stretch")


def render_download_button(
    *,
    settings: PlanningSettings,
    constraint_detail: ConstraintDetail,
    date_details: list[DateDetail],
    facility_details: list[FacilityDetail],
    facility_daily_target_details: list[FacilityDailyTargetDetail],
) -> None:
    disabled = (
        len(facility_details) == 0
        or len(date_details) == 0
        or len(facility_daily_target_details) == 0
    )

    input_file_name = (
        f"{settings.regional_office_name}_AI入力シート_"
        f"{settings.year}{settings.month:02d}.xlsx"
    )

    output_file_name = (
        f"{settings.regional_office_name}_AI出力貼付シート_"
        f"{settings.year}{settings.month:02d}.xlsx"
    )

    st.subheader("Excelファイル生成")

    if disabled:
        st.warning("Excel生成に必要なデータが不足しています。")
        return

    if not st.button("Excelファイルを生成", type="primary"):
        st.info("ボタンを押すとExcelファイルを生成します。")
        return

    try:
        input_wb = load_workbook(COPILOT_INPUT_TEMPLATE_PATH)
        output_wb = load_workbook(COPILOT_OUTPUT_TEMPLATE_PATH)

        input_data_cpa = calculate_input_data_cpa(facility_details)

        input_workbook_bytes = InputWorkbookBuilder(
            wb=input_wb,
            constraint_detail=constraint_detail,
            facility_details=facility_details,
            date_details=date_details,
            facility_daily_target_details=facility_daily_target_details,
            input_data_cpa=input_data_cpa,
        ).build()

        output_workbook_bytes = OutputWorkbookBuilder(
            wb=output_wb,
            constraint_detail=constraint_detail,
            facility_details=facility_details,
            date_details=date_details,
            facility_daily_target_details=facility_daily_target_details,
            input_data_cpa=input_data_cpa,
        ).build()

    except FileNotFoundError as exc:
        st.error("Excelテンプレートファイルが見つかりません。")
        st.exception(exc)
        return

    except Exception as exc:  # noqa: BLE001
        st.error("Excelファイルの生成に失敗しました。")
        st.exception(exc)
        return

    st.success("Excelファイルを生成しました。")

    col_input, col_output = st.columns(2)

    with col_input:
        st.download_button(
            label="AI入力用のExcelをダウンロード",
            data=input_workbook_bytes,
            file_name=input_file_name,
            mime=EXCEL_MIME_TYPE,
            on_click="ignore",
        )

    with col_output:
        st.download_button(
            label="AI出力貼付用のExcelをダウンロード",
            data=output_workbook_bytes,
            file_name=output_file_name,
            mime=EXCEL_MIME_TYPE,
            on_click="ignore",
        )


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    st.title(PAGE_TITLE)

    st.divider()
    database_name = fetch_current_database_name()
    schema_names = fetch_schema_names()

    connection_settings = render_connection_settings_section(
        database_name,
        schema_names,
    )

    if connection_settings is None:
        st.info("接続設定を確認し、「Snowflakeから読み込み」を押してください。")
        return

    st.caption(
        "現在の読み込み設定: "
        f"DB={connection_settings.database_name} / "
        f"RAW={connection_settings.raw_schema}, "
        f"STG={connection_settings.stg_schema}, "
        f"INT={connection_settings.int_schema}, "
        f"MART={connection_settings.mart_schema}"
    )

    st.divider()
    benchmark_period_keys = fetch_benchmark_period_keys(connection_settings)
    planning_settings = render_planning_settings_section(benchmark_period_keys)

    st.divider()
    regional_office_schedule_constraints = fetch_regional_office_schedule_constraints(
        connection_settings
    )
    constraint_detail = render_constraint_section(
        planning_settings,
        regional_office_schedule_constraints,
    )

    st.divider()
    facility_details = load_facility_details(connection_settings, planning_settings)

    st.divider()
    facility_daily_target_details = load_facility_daily_target_details(
        connection_settings,
        planning_settings,
    )

    st.divider()
    date_details = load_date_details(connection_settings, planning_settings)

    render_download_button(
        settings=planning_settings,
        constraint_detail=constraint_detail,
        date_details=date_details,
        facility_details=facility_details,
        facility_daily_target_details=facility_daily_target_details,
    )


if __name__ == "__main__":
    main()
