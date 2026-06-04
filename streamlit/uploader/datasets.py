"""アップロード対象データセットの定義（データのみ）。新規追加はここに1つ足すだけ。"""

from __future__ import annotations

from loaders.spec import DatasetSpec

_FM_BOOL = ["has_ds_or_satellite_bool", "ds_bool", "st_bool", "retail_bool",
            "softbank_bool", "au_bool", "rakuten_mobile_bool"]

ACTUALS = DatasetSpec(
    label="実績データ",
    table="RAW_FACILITY_ACTUALS",
    layout="wide",
    sheet=None, month_mode=True,
    header_row=3, first_col=1, fixed_n=13, key_col="施設名",
    type_map={"No": "NUMBER(38,0)", "開始日": "DATE", "終了日": "DATE",
              "面積": "VARCHAR", "スタッフ数": "VARCHAR", "実施日数": "VARCHAR"},
    default_type="VARCHAR",
    date_col_type="VARCHAR",   # 日付列は原文保持（クレンジングは縦持ちSQLで実施）
    caption="月別シートを横持ちのまま raw_facility_actuals_<yyyymm> へ CREATE OR REPLACE",
    note="※ 日付列は原文のまま保存（＠/中止/なし/不明/空など）。クレンジングは縦持ちSQLで実施します。",
)

DATE_MASTER = DatasetSpec(
    label="日付マスタ",
    table="RAW_DATE_MASTER",
    layout="flat",
    sheet="日付マスタ", header_row=1, key_col="date",
    type_map={"date": "DATE",
              "year": "NUMBER(38,0)", "month": "NUMBER(38,0)", "day": "NUMBER(38,0)",
              "week_number_yearly": "NUMBER(38,0)", "week_number_monthly": "NUMBER(38,0)",
              "is_offday": "BOOLEAN", "is_holiday": "BOOLEAN"},
    default_type="VARCHAR",
    caption="日付マスタ（「日付マスタ」シート）を RAW_DATE_MASTER へ CREATE OR REPLACE",
)

SEASONAL = DatasetSpec(
    label="季節指数マスタ",
    table="RAW_FACILITY_SEASONAL_DAILY",
    layout="wide",
    sheet="01_日別施設別（SENSE）", header_row=1, first_col=0, fixed_n=3, key_col="施設名",
    type_map={"施設コード": "NUMBER(38,0)", "施設名": "VARCHAR", "年間平均値": "FLOAT"},
    default_type="VARCHAR", date_col_type="NUMBER(38,0)",
    caption="季節指数マスタの「01_日別施設別（SENSE）」を RAW_FACILITY_SEASONAL_DAILY へ",
)

FACILITY_MASTER = DatasetSpec(
    label="施設マスタ",
    table="RAW_FACILITY_MASTER",
    layout="flat",
    sheet="facility_master", header_row=1, key_col="facility_code",
    type_map={"facility_code": "NUMBER(38,0)", **{c: "BOOLEAN" for c in _FM_BOOL}},
    default_type="VARCHAR",
    caption="施設マスタの「facility_master」シート（全列raw）を RAW_FACILITY_MASTER へ",
)

NAME_MAPPINGS = DatasetSpec(
    label="施設名マッピングマスタ",
    table="RAW_FACILITY_NAME_MAPPINGS",
    layout="flat",
    sheet="施設名マッピングマスタ", header_row=1, key_col="original_name",
    default_type="VARCHAR",
    caption="施設名マッピングマスタを RAW_FACILITY_NAME_MAPPINGS へ（original_name / mapped_name）",
)

FOOT_TRAFFIC = DatasetSpec(
    label="人流・デシルマスタ",
    table="RAW_FACILITY_FOOT_TRAFFIC_DAILY",
    layout="wide",
    sheet="01_日別施設別（SENSE）", header_row=0, first_col=0, fixed_n=3, key_col="施設名",
    type_map={"施設コード": "NUMBER(38,0)", "施設名": "VARCHAR", "年間平均値": "FLOAT"},
    default_type="VARCHAR", date_col_type="NUMBER(38,0)",
    caption="人流・デシルマスタの「01_日別施設別（SENSE）」を RAW_FACILITY_FOOT_TRAFFIC_DAILY へ",
)

DATASETS = {s.label: s for s in [
    ACTUALS, DATE_MASTER, SEASONAL, FACILITY_MASTER, NAME_MAPPINGS, FOOT_TRAFFIC,
]}
