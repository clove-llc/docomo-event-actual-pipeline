from __future__ import annotations
from pathlib import Path

PAGE_TITLE = "Copilot用Excelシート作成"

REGIONAL_OFFICE_NAMES = [
    "関信越",
    "関西",
    "九州",
    "四国",
    "首都圏",
    "中国",
    "東海",
    "東北",
    "北海道",
    "北陸",
]


APP_DIR = Path(__file__).resolve().parent

COPILOT_INPUT_TEMPLATE_PATH = APP_DIR / "templates" / "copilot_input_template.xlsx"
COPILOT_OUTPUT_TEMPLATE_PATH = APP_DIR / "templates" / "copilot_output_template.xlsx"

EXCEL_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
