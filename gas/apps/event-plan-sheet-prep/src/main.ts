const COMMON_SETTING_CELL_MAP = {
  // 対象年度
  targetYear: "C2",

  // 対象月
  targetMonth: "C3",

  // 対象月の目標値シートのURL
  targetMonthSpreadsheetUrl: "C4",

  // 対象月の制約条件シートのURL
  constraintSpreadsheetUrl: "C5",

  // 入力・出力シート_制約条件シート名
  constraintSheetName: "C6",

  // 入力・出力シート_制約条件シート_変更するセル
  constraintSheetTargetCell: "C7",

  // 入力・出力シート_インプットデータシート名
  inputDataSheetName: "C8",

  // 入力・出力シート_インプットデータシート_変更するセル
  inputDataSheetTargetCell: "C9",

  // 入力・出力シート_日付情報シート名
  dateSheetName: "C10",

  // 入力・出力シート_日付情報シート_年度を保持するセル
  dateSheetTargetYearCell: "C11",

  // 入力・出力シート_日付情報シート_月（-1）を保持するセル
  dateSheetTargetMonthCell: "C12",
} as const;

const PREP_SHEET_CELL_MAP = {
  // 準備シート_フォルダID
  prepFolderId: "C2",

  // 準備シート_テンプレートシートID
  prepTemplateFileId: "C3",

  // 準備シート_目標値シート名
  prepTargetSheetName: "C4",

  // 準備シート_目標値シート_参照URLを配置しているセル
  prepSheetTargetCell: "C5",
} as const;

const INPUT_SHEET_CELL_MAP = {
  // 入力シート_フォルダID
  inputFolderId: "C2",

  // 入力シート_テンプレートフォルダID
  inputTemplateFolderId: "C3",
} as const;

const OUTPUT_SHEET_CELL_MAP = {
  // 出力シート_フォルダID
  outputFolderId: "C2",

  // 出力シート_テンプレートフォルダID
  outputTemplateFolderId: "C3",
} as const;

// スプレッドシート上の設定値を取得するための関数
type CellMap = Record<string, string>;

type SettingsFromCellMap<T extends CellMap> = {
  [K in keyof T]: string;
};

type CommonSettings = {
  targetYear: string;
  targetMonth: number;
  targetMonthZeroBased: number;
  targetMonthSpreadsheetUrl: string;
  constraintSpreadsheetUrl: string;
  constraintSheetName: string;
  constraintSheetTargetCell: string;
  inputDataSheetName: string;
  inputDataSheetTargetCell: string;
  dateSheetName: string;
  dateSheetTargetYearCell: string;
  dateSheetTargetMonthCell: string;
};

function getCommonSettings(): CommonSettings {
  const raw = getSettingValuesFromSpecifiedConfig(
    "共通設定シート",
    COMMON_SETTING_CELL_MAP,
  );

  return {
    ...raw,
    targetMonth: Number(raw.targetMonth),
    targetMonthZeroBased: Number(raw.targetMonth) - 1,
  };
}

function getPrepSettings() {
  return getSettingValuesFromSpecifiedConfig(
    "準備シート_設定値",
    PREP_SHEET_CELL_MAP,
  );
}

function getInputSettings() {
  return getSettingValuesFromSpecifiedConfig(
    "インプットシート_設定値",
    INPUT_SHEET_CELL_MAP,
  );
}

function getOutputSettings() {
  return getSettingValuesFromSpecifiedConfig(
    "アウトプットシート_設定値",
    OUTPUT_SHEET_CELL_MAP,
  );
}

function getSettingValuesFromSpecifiedConfig<T extends CellMap>(
  configSheetName: string,
  config: T,
): SettingsFromCellMap<T> {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(configSheetName);

  if (!sheet) {
    throw new Error(`シート「${configSheetName}」が見つかりません。`);
  }

  const settings = {} as SettingsFromCellMap<T>;
  const errors: string[] = [];

  for (const key in config) {
    const cellAddress = config[key];
    const value = sheet.getRange(cellAddress).getValue();

    if (
      value === "" ||
      value === null ||
      value === undefined ||
      String(value).trim() === ""
    ) {
      errors.push(`[${cellAddress}] の値が空です。`);
    } else {
      settings[key] = String(value) as SettingsFromCellMap<T>[Extract<
        keyof T,
        string
      >];
    }
  }

  if (errors.length > 0) {
    const errorMsg = `設定シートの入力内容に不備があります。\n${errors.join("\n")}`;
    Browser.msgBox(errorMsg);
    throw new Error(errorMsg);
  }

  return settings;
}

// 指定のフォルダの中身を別のフォルダにコピーするための関数
function copyFolderContents(
  sourceFolder: GoogleAppsScript.Drive.Folder,
  destFolder: GoogleAppsScript.Drive.Folder,
) {
  const files = sourceFolder.getFiles();

  while (files.hasNext()) {
    const file = files.next();

    file.makeCopy(file.getName(), destFolder);
  }
}

function replaceYearAndMonthInFiles(
  targetFiles: GoogleAppsScript.Drive.FileIterator,
  targetSheetName: string,
  targetYearCell: string,
  targetMonthCell: string,
  targetYear: string,
  targetMonthZeroBased: number,
) {
  let processedCount = 0;
  const activeSpreadsheetId = SpreadsheetApp.getActiveSpreadsheet().getId();

  while (targetFiles.hasNext()) {
    const targetFile = targetFiles.next();
    const targetSpreadsheetId = targetFile.getId();

    if (targetSpreadsheetId === activeSpreadsheetId) {
      continue;
    }

    try {
      const targetSpreadsheet = SpreadsheetApp.openById(targetSpreadsheetId);
      const targetSheet = targetSpreadsheet.getSheetByName(targetSheetName);

      if (!targetSheet) {
        Logger.log(
          `スキップ: [${targetFile.getName()}] にシート「${targetSheetName}」が存在しません。`,
        );
        continue;
      }

      targetSheet.getRange(targetYearCell).setValue(targetYear);
      targetSheet.getRange(targetMonthCell).setValue(targetMonthZeroBased);

      Logger.log(
        `更新成功: [${targetFile.getName()}] の ${targetSheetName}!${targetYearCell}, ${targetMonthCell}`,
      );

      processedCount++;
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      Logger.log(`エラー発生 [${targetFile.getName()}]: ${message}`);
    }
  }

  Logger.log(
    `完了！ 合計 ${processedCount} 件のスプレッドシートを更新しました。`,
  );
}

function replaceImportRangeSpreadsheetUrlInFiles(
  targetFiles: GoogleAppsScript.Drive.FileIterator,
  targetSheetName: string,
  targetCell: string,
  targetSpreadsheetUrl: string,
) {
  let processedCount = 0;
  const activeSpreadsheetId = SpreadsheetApp.getActiveSpreadsheet().getId();

  while (targetFiles.hasNext()) {
    const targetFile = targetFiles.next();
    const targetSpreadsheetId = targetFile.getId();

    if (targetSpreadsheetId === activeSpreadsheetId) {
      continue;
    }

    try {
      const targetSpreadsheet = SpreadsheetApp.openById(targetSpreadsheetId);
      const targetSheet = targetSpreadsheet.getSheetByName(targetSheetName);

      if (!targetSheet) {
        Logger.log(
          `スキップ: [${targetFile.getName()}] にシート「${targetSheetName}」が存在しません。`,
        );
        continue;
      }

      targetSheet.getRange(targetCell).setValue(targetSpreadsheetUrl);

      Logger.log(
        `置換成功: [${targetFile.getName()}] の ${targetSheetName}!${targetCell}`,
      );

      processedCount++;
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      Logger.log(`エラー発生 [${targetFile.getName()}]: ${message}`);
    }
  }

  Logger.log(
    `完了！ 合計 ${processedCount} 件のスプレッドシートを更新しました。`,
  );
}

function setupPrepSpreadsheet(commonSettings: CommonSettings) {
  const { targetMonth, targetMonthSpreadsheetUrl } = commonSettings;

  const {
    prepFolderId,
    prepTemplateFileId,
    prepTargetSheetName,
    prepSheetTargetCell,
  } = getPrepSettings();

  const prepFolder = DriveApp.getFolderById(prepFolderId);
  const prepTemplateFile = DriveApp.getFileById(prepTemplateFileId);

  Logger.log("テンプレートシートをもとに、新規の月の準備シートを作成中...");
  const newPrepFile = prepTemplateFile.makeCopy(
    targetMonth + "月分",
    prepFolder,
  );
  Logger.log("作成完了。");

  const newPrepTargetSheet = SpreadsheetApp.openById(
    newPrepFile.getId(),
  ).getSheetByName(prepTargetSheetName);

  if (!newPrepTargetSheet) {
    throw new Error(
      `作成したファイルにシート「${prepTargetSheetName}」が存在しません。`,
    );
  }

  Logger.log("準備シートの目標値参照URLを更新中...");
  newPrepTargetSheet
    .getRange(prepSheetTargetCell)
    .setValue(targetMonthSpreadsheetUrl);
  Logger.log("更新完了。");

  return newPrepFile.getUrl();
}

function setupInputSpreadSheets(
  commonSettings: CommonSettings,
  newPrepFileUrl: string,
) {
  const {
    targetMonth,
    targetMonthZeroBased,
    targetYear,
    constraintSpreadsheetUrl,
    constraintSheetName,
    constraintSheetTargetCell,
    inputDataSheetName,
    inputDataSheetTargetCell,
    dateSheetName,
    dateSheetTargetYearCell,
    dateSheetTargetMonthCell,
  } = commonSettings;

  const { inputFolderId, inputTemplateFolderId } = getInputSettings();

  const inputFolder = DriveApp.getFolderById(inputFolderId);

  Logger.log("新規の月のインプットシートを保管するフォルダを作成中...");
  const newInputFolder = inputFolder.createFolder(targetMonth + "月分");
  Logger.log("作成完了。");

  const inputTemplateFolder = DriveApp.getFolderById(inputTemplateFolderId);

  Logger.log(
    "テンプレートシートをもとに、新規の月のインプットシートを作成中...",
  );
  copyFolderContents(inputTemplateFolder, newInputFolder);
  Logger.log("作成完了。");

  Logger.log("インプットシートの参照URLを更新中...");

  Logger.log("1. 制約条件シートのURLを更新中...");
  replaceImportRangeSpreadsheetUrlInFiles(
    newInputFolder.getFilesByType("application/vnd.google-apps.spreadsheet"),
    constraintSheetName,
    constraintSheetTargetCell,
    constraintSpreadsheetUrl,
  );
  Logger.log("更新完了。");

  Logger.log("2. インプットデータシートのURLを更新中...");
  replaceImportRangeSpreadsheetUrlInFiles(
    newInputFolder.getFilesByType("application/vnd.google-apps.spreadsheet"),
    inputDataSheetName,
    inputDataSheetTargetCell,
    newPrepFileUrl,
  );
  Logger.log("更新完了。");

  Logger.log("インプットシートの日付情報を更新中...");
  replaceYearAndMonthInFiles(
    newInputFolder.getFilesByType("application/vnd.google-apps.spreadsheet"),
    dateSheetName,
    dateSheetTargetYearCell,
    dateSheetTargetMonthCell,
    targetYear,
    targetMonthZeroBased,
  );
  Logger.log("更新完了。");
}

function setupOutputSpreadSheets(
  commonSettings: CommonSettings,
  newPrepFileUrl: string,
) {
  const {
    targetMonth,
    targetMonthZeroBased,
    targetYear,
    constraintSpreadsheetUrl,
    constraintSheetName,
    constraintSheetTargetCell,
    inputDataSheetName,
    inputDataSheetTargetCell,
    dateSheetName,
    dateSheetTargetYearCell,
    dateSheetTargetMonthCell,
  } = commonSettings;

  const { outputFolderId, outputTemplateFolderId } = getOutputSettings();

  const outputFolder = DriveApp.getFolderById(outputFolderId);

  Logger.log("新規の月のアウトプットシートを保管するフォルダを作成中...");
  const newOutputFolder = outputFolder.createFolder(targetMonth + "月分");
  Logger.log("作成完了。");

  const outputTemplateFolder = DriveApp.getFolderById(outputTemplateFolderId);

  Logger.log(
    "テンプレートシートをもとに、新規の月のアウトプットシートを作成中...",
  );
  copyFolderContents(outputTemplateFolder, newOutputFolder);
  Logger.log("作成完了。");

  Logger.log("アウトプットシートの参照URLを更新中...");

  Logger.log("1. 制約条件シートのURLを更新中...");
  replaceImportRangeSpreadsheetUrlInFiles(
    newOutputFolder.getFilesByType("application/vnd.google-apps.spreadsheet"),
    constraintSheetName,
    constraintSheetTargetCell,
    constraintSpreadsheetUrl,
  );
  Logger.log("更新完了。");

  Logger.log("2. インプットデータシートのURLを更新中...");
  replaceImportRangeSpreadsheetUrlInFiles(
    newOutputFolder.getFilesByType("application/vnd.google-apps.spreadsheet"),
    inputDataSheetName,
    inputDataSheetTargetCell,
    newPrepFileUrl,
  );
  Logger.log("更新完了。");

  Logger.log("アウトプットシートの日付情報を更新中...");
  replaceYearAndMonthInFiles(
    newOutputFolder.getFilesByType("application/vnd.google-apps.spreadsheet"),
    dateSheetName,
    dateSheetTargetYearCell,
    dateSheetTargetMonthCell,
    targetYear,
    targetMonthZeroBased,
  );
  Logger.log("更新完了。");
}

function setupNewMonthSpreadSheets() {
  const commonSettings = getCommonSettings();

  Logger.log("----- 新規の月の準備シートの作成を開始します。 -----");
  const newPrepFileUrl = setupPrepSpreadsheet(commonSettings);

  Logger.log("----- 新規の月のインプットシートの作成を開始します。 -----");
  setupInputSpreadSheets(commonSettings, newPrepFileUrl);

  Logger.log("----- 新規の月のアウトプットシートの作成を開始します。 -----");
  setupOutputSpreadSheets(commonSettings, newPrepFileUrl);

  Logger.log(
    "----- 準備シート・インプットシート・アウトプットシートの更新が完了しました。 -----",
  );
}
