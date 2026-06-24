"""アップロード対象データセットの定義（データのみ）。新規追加はここに1つ足すだけ。"""

from __future__ import annotations

from loaders.spec import DatasetSpec

_FM_BOOL = [
    "has_ds_or_satellite_bool",
    "ds_bool",
    "st_bool",
    "retail_bool",
    "softbank_bool",
    "au_bool",
    "rakuten_mobile_bool",
]

ACTUALS = DatasetSpec(
    label="実績データ",
    table="RAW_FACILITY_ACTUALS",
    layout="wide",
    sheet=None,
    month_mode=True,
    header_row=3,
    first_col=1,
    fixed_n=13,
    key_col="施設名",
    type_map={
        "No": "NUMBER(38,0)",
        "開始日": "DATE",
        "終了日": "DATE",
        "面積": "VARCHAR",
        "スタッフ数": "VARCHAR",
        "実施日数": "VARCHAR",
    },
    default_type="VARCHAR",
    date_col_type="VARCHAR",  # 日付列は原文保持（クレンジングは縦持ちSQLで実施）
    caption="月別シートを横持ちのまま raw_facility_actuals_<yyyymm> へ CREATE OR REPLACE",
    note="※ 日付列は原文のまま保存（＠/中止/なし/不明/空など）。クレンジングは縦持ちSQLで実施します。",
)

DATE_MASTER = DatasetSpec(
    label="日付マスタ",
    table="RAW_DATE_MASTER",
    layout="flat",
    sheet="日付マスタ",
    header_row=1,
    key_col="date",
    type_map={
        "date": "DATE",
        "year": "NUMBER(38,0)",
        "month": "NUMBER(38,0)",
        "day": "NUMBER(38,0)",
        "week_number_yearly": "NUMBER(38,0)",
        "week_number_monthly": "NUMBER(38,0)",
        "is_offday": "BOOLEAN",
        "is_holiday": "BOOLEAN",
    },
    default_type="VARCHAR",
    caption="日付マスタ（「日付マスタ」シート）を RAW_DATE_MASTER へ CREATE OR REPLACE",
)

FACILITY_MASTER = DatasetSpec(
    label="施設マスタ",
    table="RAW_FACILITY_MASTER",
    layout="flat",
    sheet="facility_master",
    header_row=1,
    key_col="facility_code",
    type_map={"facility_code": "NUMBER(38,0)", **{c: "BOOLEAN" for c in _FM_BOOL}},
    default_type="VARCHAR",
    caption="施設マスタの「facility_master」シート（全列raw）を RAW_FACILITY_MASTER へ",
)

NAME_MAPPINGS = DatasetSpec(
    label="施設名マッピングマスタ",
    table="RAW_FACILITY_NAME_MAPPINGS",
    layout="flat",
    sheet="施設名マッピングマスタ",
    header_row=1,
    key_col="original_name",
    default_type="VARCHAR",
    caption="施設名マッピングマスタを RAW_FACILITY_NAME_MAPPINGS へ（original_name / mapped_name）",
)

FOOT_TRAFFIC = DatasetSpec(
    label="日別人流データ",
    table="RAW_FACILITY_FOOT_TRAFFIC_DAILY",
    layout="wide",
    sheet="01_日別施設別（SENSE）",
    header_row=0,
    first_col=0,
    fixed_n=3,
    key_col="施設名",
    type_map={"施設コード": "NUMBER(38,0)", "施設名": "VARCHAR", "年間平均値": "FLOAT"},
    default_type="VARCHAR",
    date_col_type="NUMBER(38,0)",
    caption="日別人流データの「01_日別施設別（SENSE）」を RAW_FACILITY_FOOT_TRAFFIC_DAILY へ",
)

KDDI_FOOT_TRAFFIC = DatasetSpec(
    label="KDDI人流データ",
    table="RAW_KDDI_FOOT_TRAFFIC",
    layout="flat",
    sheet="KDDI人流データ",
    header_row=0,
    key_col="facility_code",
    rename={
        "No": "facility_code",
        "施設名": "facility_name",
        "全日|TTL": "foot_traffic_total",
    },
    type_map={"facility_code": "NUMBER(38,0)", "foot_traffic_total": "NUMBER(38,0)"},
    default_type="VARCHAR",
    caption="人流・デシルマスタの「KDDI人流データ」シートを RAW_KDDI_FOOT_TRAFFIC へ（施設別の年間人流TTL）",
)

DATE_FLAG = DatasetSpec(
    label="日付フラグマスタ",
    table="RAW_DATE_FLAG",
    layout="flat",
    sheet="日付フラグマスタ",
    header_row=0,
    usecols="B:C",
    key_col="date",
    rename={"日付": "date", "フラグ名": "date_flag"},
    type_map={"date": "DATE"},
    default_type="VARCHAR",
    caption="人流・デシルマスタの「日付フラグマスタ」シート(B:C)を RAW_DATE_FLAG へ（日付→フラグ名）",
)

FACILITY_SCHEDULE_CONSTRAINT = DatasetSpec(
    label="施設別スケジュール制限マスタ",
    table="RAW_FACILITY_SCHEDULE_CONSTRAINTS_MASTER",
    layout="flat",
    sheet="施設別スケジュール制限マスタ",
    rename={
        "施設コード": "FACILITY_CODE",
        "施設名": "FACILITY_NAME",
        "月当たりの開催上限": "MONTHLY_EVENT_LIMIT",
        "稼働曜日": "OPERATING_DAYS",
    },
    type_map={
        "施設コード": "NUMBER",
        "施設名": "VARCHAR",
        "月当たりの開催上限": "VARCHAR",
        "稼働曜日": "VARCHAR",
    },
    caption="施設別スケジュール制限マスタの「施設別スケジュール制限マスタ」シート(A:D)を RAW_FACILITY_SCHEDULE_CONSTRAINTS_MASTER へ",
)

REGIONAL_OFFICE_SCHEDULE_CONSTRAINT = DatasetSpec(
    label="支社別スケジュール制限マスタ",
    table="RAW_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER",
    layout="flat",
    sheet="支社別スケジュール制限マスタ",
    rename={
        "支社名": "REGIONAL_OFFICE_NAME",
        "稼働ライン（日当たり）": "DAILY_EVENT_LIMIT",
        "稼働曜日": "OPERATING_DAYS",
    },
    type_map={
        "支社名": "VARCHAR",
        "稼働ライン（日当たり）": "NUMBER",
        "稼働曜日": "VARCHAR",
    },
    caption="支社別スケジュール制限マスタの「支社別スケジュール制限マスタ」シート(A:C)を RAW_REGIONAL_OFFICE_SCHEDULE_CONSTRAINTS_MASTER へ",
)

EXCLUDED_FACILITY = DatasetSpec(
    label="除外対象施設マスタ",
    table="RAW_EXCLUDED_FACILITY_MASTER",
    layout="flat",
    sheet="除外対象施設マスタ",
    rename={"施設名": "FACILITY_NAME"},
    type_map={"施設名": "VARCHAR"},
    caption="除外対象施設マスタの「除外対象施設マスタ」シート(A:A)を RAW_EXCLUDED_FACILITY_MASTER へ",
)

TARGET_CPA = DatasetSpec(
    label="施設別目標CPAマスタ",
    table="RAW_FACILITY_TARGET_CPA_MASTER",
    layout="flat",
    sheet="施設別目標CPAマスタ",
    rename={"施設名": "FACILITY_NAME", "CPA": "CPA"},
    type_map={"施設名": "VARCHAR", "CPA": "NUMBER"},
    caption="施設別目標CPAマスタの「施設別目標CPAマスタ」シート(A:B)を RAW_FACILITY_TARGET_CPA_MASTER へ",
)

DATASETS = {
    s.label: s
    for s in [
        ACTUALS,
        DATE_MASTER,
        FACILITY_MASTER,
        NAME_MAPPINGS,
        FOOT_TRAFFIC,
        KDDI_FOOT_TRAFFIC,
        DATE_FLAG,
        FACILITY_SCHEDULE_CONSTRAINT,
        REGIONAL_OFFICE_SCHEDULE_CONSTRAINT,
        EXCLUDED_FACILITY,
        TARGET_CPA,
    ]
}
