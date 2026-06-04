"""データセット定義（DatasetSpec）と接続コンテキスト（LoadContext）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class LoadContext:
    """接続まわりの状態（SiS セッション or ローカル secrets）。"""
    session: object | None
    cfg: dict | None
    db: str
    schema: str


@dataclass(frozen=True)
class DatasetSpec:
    """1データセット（マスタ/実績）の取込仕様。UIもDDLも casting もこれ1つで駆動する。

    layout:
      - "wide": 固定列 + 動的な日付列（実績/季節指数/人流）。fixed_n・date_col_type を使う。
      - "flat": そのままの表（日付マスタ/施設マスタ/施設名マッピング）。
    """
    label: str                      # セレクタ表示名
    table: str                      # 出力テーブル名（month_mode 時は接頭辞）
    layout: Literal["wide", "flat"]
    sheet: str | None = None        # 固定シート名。None は月別選択（month_mode）
    header_row: int = 0             # 0始まりのヘッダー行
    first_col: int = 0              # 先頭から無視する列数（A列空など）
    fixed_n: int | None = None      # wide: 固定列数
    key_col: str | None = None      # この列が空の行は除外
    type_map: dict[str, str] = field(default_factory=dict)  # 列名→SQL型
    default_type: str = "VARCHAR"   # type_map 未掲載列の既定型
    date_col_type: str | None = None  # wide: 日付列の型
    month_mode: bool = False        # 実績: 月別シート選択＋テーブル名に _yyyymm
    caption: str = ""               # 画面上部の説明
    note: str = ""                  # プレビュー下の補足

    def type_for(self, col: str, date_names: list[str]) -> str:
        """列の SQL 型を返す（DDLと casting の両方がこれを使う）。"""
        if col in self.type_map:
            return self.type_map[col]
        if self.layout == "wide" and self.date_col_type and col in date_names:
            return self.date_col_type
        return self.default_type
