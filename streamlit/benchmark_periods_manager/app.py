from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from config import PAGE_TITLE
from entities import BenchmarkPeriod
from snowflake_repository import (
    init_table,
    apply_benchmark_period_updates_and_deletes,
    clear_benchmark_periods_cache,
    fetch_benchmark_periods,
    insert_benchmark_period,
)

FLASH_MESSAGE_KEY = "flash_message"


def render_flash_message() -> None:
    message = st.session_state.pop(FLASH_MESSAGE_KEY, None)

    if message:
        st.success(message)


def to_date_or_none(value: Any) -> date | None:
    if pd.isna(value):
        return None

    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def build_benchmark_period(
    period_start_date: date,
    period_end_date: date,
) -> BenchmarkPeriod:
    return BenchmarkPeriod(
        benchmark_period_key=f"{period_start_date.strftime('%Y_%m')}_{period_end_date.strftime('%Y_%m')}",
        benchmark_period_name=(
            f"{period_start_date.year}年{period_start_date.month}月"
            f"〜{period_end_date.year}年{period_end_date.month}月"
        ),
        period_start_date=period_start_date,
        period_end_date=period_end_date,
        period_month_count=(period_end_date.year - period_start_date.year) * 12
        + period_end_date.month
        - period_start_date.month
        + 1,
    )


def to_editable_dataframe(periods: list[BenchmarkPeriod]) -> pd.DataFrame:
    df = pd.DataFrame(
        [asdict(period) for period in periods],
        columns=list(BenchmarkPeriod.__dataclass_fields__.keys()),
    )
    df.insert(0, "delete", False)
    return df


def validate_period_dates(
    period_start_date: date | None,
    period_end_date: date | None,
) -> list[str]:
    errors: list[str] = []

    if period_start_date is None:
        errors.append("過去実績期間の開始日 を入力してください。")

    if period_end_date is None:
        errors.append("過去実績期間の終了日 を入力してください。")

    if (
        period_start_date is not None
        and period_end_date is not None
        and period_start_date > period_end_date
    ):
        errors.append(
            "過去実績期間の開始日 は 過去実績期間の終了日 以前にしてください。"
        )

    return errors


def validate_update_delete_inputs(
    edited_df: pd.DataFrame,
    benchmark_periods: list[BenchmarkPeriod],
) -> tuple[list[str], list[tuple[str, BenchmarkPeriod]], list[str]]:
    errors: list[str] = []
    update_rows: list[tuple[str, BenchmarkPeriod]] = []
    delete_keys: list[str] = []
    final_periods: list[BenchmarkPeriod] = []

    before_periods_by_key = {
        period.benchmark_period_key: period for period in benchmark_periods
    }

    df = edited_df.dropna(how="all").copy()

    for row_no, (_, row) in enumerate(df.iterrows(), start=1):
        original_benchmark_period_key = str(row.get("benchmark_period_key"))
        before_period = before_periods_by_key.get(original_benchmark_period_key)
        should_delete = bool(row.get("delete"))

        if before_period is None:
            errors.append(f"{row_no}行目: benchmark_period_key が不正です。")
            continue

        if should_delete:
            delete_keys.append(original_benchmark_period_key)
            continue

        period_start_date = to_date_or_none(row.get("period_start_date"))
        period_end_date = to_date_or_none(row.get("period_end_date"))

        row_errors = validate_period_dates(
            period_start_date,
            period_end_date,
        )

        for error in row_errors:
            errors.append(f"{row_no}行目: {error}")

        if row_errors:
            continue

        assert period_start_date is not None
        assert period_end_date is not None

        after_period = build_benchmark_period(
            period_start_date,
            period_end_date,
        )

        final_periods.append(after_period)

        if (
            before_period.period_start_date == after_period.period_start_date
            and before_period.period_end_date == after_period.period_end_date
        ):
            continue

        update_rows.append(
            (
                original_benchmark_period_key,
                after_period,
            )
        )

    duplicated_keys = (
        pd.Series([period.benchmark_period_key for period in final_periods])
        .loc[lambda series: series.duplicated()]
        .drop_duplicates()
        .tolist()
    )

    for key in duplicated_keys:
        errors.append(f"benchmark_period_key が重複しています: {key}")

    return errors, update_rows, delete_keys


def render_add_section(existing_periods: list[BenchmarkPeriod]) -> None:
    st.subheader("追加")

    with st.form("add_benchmark_period_form"):
        period_start_date = st.date_input(
            "過去実績期間の開始日",
            value=None,
            format="YYYY-MM-DD",
        )

        period_end_date = st.date_input(
            "過去実績期間の終了日",
            value=None,
            format="YYYY-MM-DD",
        )

        submitted = st.form_submit_button(
            "追加",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    errors = validate_period_dates(
        period_start_date,
        period_end_date,
    )

    if errors:
        for error in errors:
            st.error(error)
        return

    assert period_start_date is not None
    assert period_end_date is not None

    benchmark_period = build_benchmark_period(
        period_start_date,
        period_end_date,
    )

    existing_keys = {period.benchmark_period_key for period in existing_periods}

    if benchmark_period.benchmark_period_key in existing_keys:
        st.error(
            "同じ期間のデータがすでに存在します。"
            f" benchmark_period_key: {benchmark_period.benchmark_period_key}"
        )
        return

    with st.spinner("Snowflakeへ追加中です..."):
        try:
            insert_benchmark_period(benchmark_period)
            clear_benchmark_periods_cache()
        except Exception as exc:  # noqa: BLE001
            st.error("Snowflakeへの追加に失敗しました。")
            st.exception(exc)
            return

    st.session_state[FLASH_MESSAGE_KEY] = (
        "追加しました。" f" 開始日：{period_start_date}・終了日：{period_end_date}"
    )

    st.rerun()


def render_update_delete_section(benchmark_periods: list[BenchmarkPeriod]) -> None:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("更新・削除")

    with col2:
        st.caption(
            "※ セルを変更した後は、一度Enterキーを押すか、別のセルをクリックして確定させてから保存ボタンを押してください。"
        )

    if not benchmark_periods:
        st.info("更新・削除対象のデータがありません。")
        return

    with st.form("benchmark_period_update_delete_form"):
        edited_df = st.data_editor(
            to_editable_dataframe(benchmark_periods),
            key="benchmark_period_update_delete_editor",
            num_rows="fixed",
            hide_index=True,
            width="stretch",
            disabled=[
                "benchmark_period_key",
                "benchmark_period_name",
                "period_month_count",
            ],
            column_config={
                "delete": st.column_config.CheckboxColumn(
                    "削除",
                    help="削除する行にチェックを入れてください。",
                    default=False,
                ),
                "benchmark_period_key": st.column_config.TextColumn(
                    "過去実績期間キー",
                    help="period_start_date / period_end_date から保存時に再生成します。",
                ),
                "benchmark_period_name": st.column_config.TextColumn(
                    "過去実績期間名",
                    help="period_start_date / period_end_date から保存時に再生成します。",
                ),
                "period_start_date": st.column_config.DateColumn(
                    "開始日",
                    format="YYYY-MM-DD",
                    required=True,
                ),
                "period_end_date": st.column_config.DateColumn(
                    "終了日",
                    format="YYYY-MM-DD",
                    required=True,
                ),
                "period_month_count": st.column_config.NumberColumn(
                    "期間月数",
                    help="period_start_date / period_end_date から保存時に再計算します。",
                    min_value=1,
                    step=1,
                    format="%d",
                ),
            },
        )

        submitted = st.form_submit_button(
            "更新・削除を保存",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    errors, update_rows, delete_keys = validate_update_delete_inputs(
        edited_df, benchmark_periods
    )

    if errors:
        st.error("保存できません。入力内容を確認してください。")
        for error in errors:
            st.write(f"- {error}")
        return

    try:
        with st.spinner("Snowflakeへ保存中です..."):
            result = apply_benchmark_period_updates_and_deletes(
                update_rows,
                delete_keys,
            )
            clear_benchmark_periods_cache()

    except Exception as exc:  # noqa: BLE001
        st.error("Snowflakeへの保存に失敗しました。")
        st.exception(exc)
        return

    st.session_state[FLASH_MESSAGE_KEY] = (
        "保存しました。" f"更新: {result['updated']}件・削除: {result['deleted']}件"
    )

    st.rerun()


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    st.title(PAGE_TITLE)

    init_table()
    render_flash_message()

    try:
        benchmark_periods = fetch_benchmark_periods()
    except Exception as exc:  # noqa: BLE001
        st.error("Snowflakeから基準期間マスタを取得できませんでした。")
        st.exception(exc)
        st.stop()

    col_add, col_update_delete = st.columns([1, 3])

    with col_add:
        render_add_section(benchmark_periods)

    with col_update_delete:
        render_update_delete_section(benchmark_periods)


if __name__ == "__main__":
    main()
