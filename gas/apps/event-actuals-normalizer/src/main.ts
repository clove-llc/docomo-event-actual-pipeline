type RawCellValue = string | number | boolean | Date | null;

type OutputRow = [
  string, // source_sheet_name
  string, // facility_name
  string, // event_date
  string | number | boolean | null, // actual_value
];

type DateColumn = {
  index: number;
  eventDate: string;
};

const CONFIG = {
  outputSheetName: "import_event_actuals",

  headerRow: 4,
  dataStartRow: 5,

  facilityNameColumn: 6, // F（施設名）
  dateStartColumn: 15, // O（日付開始列）
  dateEndColumn: 45, // AS（日付終了列）

  outputHeaders: [
    "source_sheet_name",
    "facility_name",
    "event_date",
    "actual_value",
  ],
} as const;

/**
 * 月別シートの横持ちイベント実績を縦持ち化し、
 * import_event_actuals シートへ出力する。
 */
function unpivotEventActuals(): void {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const outputSheet = getOrCreateSheet_(spreadsheet, CONFIG.outputSheetName);

  const outputRows: OutputRow[] = [];

  for (const sheet of spreadsheet.getSheets()) {
    const sheetName = sheet.getName();

    if (sheetName === CONFIG.outputSheetName) {
      continue;
    }

    const lastRow = sheet.getLastRow();

    if (lastRow < CONFIG.dataStartRow) {
      continue;
    }

    const values = sheet
      .getRange(1, 1, lastRow, CONFIG.dateEndColumn)
      .getValues() as RawCellValue[][];

    const headerValues = values[CONFIG.headerRow - 1];
    const dateColumns = getDateColumns_(headerValues);

    if (dateColumns.length === 0) {
      continue;
    }

    for (
      let rowIndex = CONFIG.dataStartRow - 1;
      rowIndex < values.length;
      rowIndex++
    ) {
      const row = values[rowIndex];
      const facilityName = String(row[CONFIG.facilityNameColumn - 1]);

      if (!facilityName) {
        continue;
      }

      for (const { index, eventDate } of dateColumns) {
        const actualValue = normalizeActualValue_(row[index]);

        if (actualValue === null) {
          continue;
        }

        outputRows.push([sheetName, facilityName, eventDate, actualValue]);
      }
    }
  }

  writeOutput_(outputSheet, outputRows);
}

/**
 * O列〜AS列のうち、ヘッダーが日付として解釈できる列だけを返す。
 */
function getDateColumns_(headerValues: RawCellValue[]): DateColumn[] {
  const dateColumns: DateColumn[] = [];

  for (let col = CONFIG.dateStartColumn; col <= CONFIG.dateEndColumn; col++) {
    const index = col - 1;
    const eventDate = parseDate_(headerValues[index]);

    if (eventDate) {
      dateColumns.push({ index, eventDate });
    }
  }

  return dateColumns;
}

/**
 * 日付ヘッダーを yyyy-MM-dd に変換する。
 */
function parseDate_(value: RawCellValue): string | null {
  if (value instanceof Date && !isNaN(value.getTime())) {
    return formatDate_(value);
  }

  if (typeof value !== "string") {
    return null;
  }

  const text = value.trim();

  if (!text) {
    return null;
  }

  const match = text.match(/^(\d{4})[\/\-年](\d{1,2})[\/\-月](\d{1,2})日?$/);

  if (!match) {
    return null;
  }

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);

  const isValidDate =
    date.getFullYear() === year &&
    date.getMonth() === month - 1 &&
    date.getDate() === day;

  return isValidDate ? formatDate_(date) : null;
}

/**
 * 実績値をraw転送用に正規化する。
 */
function normalizeActualValue_(value: RawCellValue): string | null {
  if (typeof value === "number") {
    return String(value);
  }

  if (typeof value !== "string") {
    return null;
  }

  const text = value.trim();

  if (!text) {
    return null;
  }

  if (text === "＠" || text === "@" || text === "中止" || text === "確認中") {
    return "NULL";
  }

  return text === "なし" ? "0" : null;
}

/**
 * 出力先シートを洗い替えする。
 */
function writeOutput_(
  sheet: GoogleAppsScript.Spreadsheet.Sheet,
  rows: OutputRow[],
): void {
  sheet.clearContents();

  const outputValues: Array<Array<string | number | boolean | null>> = [
    [...CONFIG.outputHeaders],
    ...rows,
  ];

  const columnCount = CONFIG.outputHeaders.length;

  sheet
    .getRange(1, 1, outputValues.length, columnCount)
    .setValues(outputValues);

  sheet.setFrozenRows(1);
}

/**
 * 出力先シートを取得。なければ作成。
 */
function getOrCreateSheet_(
  spreadsheet: GoogleAppsScript.Spreadsheet.Spreadsheet,
  sheetName: string,
): GoogleAppsScript.Spreadsheet.Sheet {
  return (
    spreadsheet.getSheetByName(sheetName) ?? spreadsheet.insertSheet(sheetName)
  );
}

/**
 * Dateを yyyy-MM-dd に変換する。
 */
function formatDate_(date: Date): string {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), "yyyy-MM-dd");
}
