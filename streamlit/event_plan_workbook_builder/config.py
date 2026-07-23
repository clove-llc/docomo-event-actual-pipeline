from __future__ import annotations
from pathlib import Path

PAGE_TITLE = "Copilot用Excelシート作成"

APP_DIR = Path(__file__).resolve().parent

COPILOT_INPUT_TEMPLATE_PATH = APP_DIR / "templates" / "copilot_input_template.xlsx"
COPILOT_OUTPUT_TEMPLATE_PATH = APP_DIR / "templates" / "copilot_output_template.xlsx"
