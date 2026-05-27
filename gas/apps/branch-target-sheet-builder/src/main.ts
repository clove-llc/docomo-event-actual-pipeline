const REGIONAL_OFFICE_SS_URL_MAP: { [key: string]: string } = {
  北陸: "https://docs.google.com/spreadsheets/d/1wRZqrzCAcGm97FU-y0JRVUou2ahUOHV0HP8sUnnRx0w/edit?usp=drive_link",
  北海道:
    "https://docs.google.com/spreadsheets/d/1wU-PNMipxhqWZwCGL41OAxc4_AE2a9PHWe9yhCrYFmk/edit?usp=drive_link",
  東北: "https://docs.google.com/spreadsheets/d/1C-mZro3leIe9jFKavM-Xtr08gF6k4uKCxnqsaL2ARsQ/edit?usp=drive_link",
  東海: "https://docs.google.com/spreadsheets/d/1FOxQoFlY_bmTa6KdyD9rQz1ZLXkzgZatSsNfePEraws/edit?usp=drive_link",
  中国: "https://docs.google.com/spreadsheets/d/1b3gcMPz9Kqdq_qvlZqMr9lvTnb7bzwCBhw-ZSRXngpU/edit?usp=drive_link",
  首都圏:
    "https://docs.google.com/spreadsheets/d/1J8nsdAu6XiDWSQTLIQ4gfKpeVsjPu_TkXDP-gm9Gcbk/edit?usp=drive_link",
  四国: "https://docs.google.com/spreadsheets/d/1JCQkRMDM15ToQo-LT1dkEpXEs8mAiRGNmqxZaE6-hkA/edit?usp=drive_link",
  九州: "https://docs.google.com/spreadsheets/d/1a9UDqISPBkzZYk6eh88sJXUwTAJOdwhMkzZdsbpKueI/edit?usp=drive_link",
  関西: "https://docs.google.com/spreadsheets/d/1W8goDPbYAtc8jXn52s2LzFRybTNVX_CT3rwJ8HqgWIE/edit?usp=drive_link",
  関信越:
    "https://docs.google.com/spreadsheets/d/1_MgOE1LMweJTX98yjsVC3W25bi88CjZifW7lIKjZtyU/edit?usp=drive_link",
};

const DATA_START_ROW = 13;
const REGIONAL_OFFICE_COL = 6;
const BRANCH_OFFICE_COL = 7;

function splitByBranchOffice() {
  const targetSpreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const planningSheet = targetSpreadsheet.getSheetByName(
    "計画策定シート（仮） のFB版_5パターン分",
  );

  if (!planningSheet) {
    Logger.log(
      "「計画策定シート（仮） のFB版_5パターン分」シートが見つかりません。",
    );
    return;
  }

  const lastRow = planningSheet.getLastRow();
  const lastCol = planningSheet.getLastColumn();
  Logger.log(
    `「計画策定シート（仮） のFB版_5パターン分」シートの最終行: ${lastRow}, 最終列: ${lastCol}`,
  );

  Logger.log(
    `「計画策定シート（仮） のFB版_5パターン分」シートのデータ範囲: ${DATA_START_ROW}行目から${lastRow}行目まで、1列目から${lastCol}列目までを二次元配列として取得中...`,
  );
  const planningList = planningSheet
    .getRange(DATA_START_ROW, 1, lastRow - DATA_START_ROW + 1, lastCol)
    .getValues();
  Logger.log(
    `データの取得が完了しました。取得したデータの行数: ${planningList.length}, 列数: ${planningList[0].length}`,
  );

  const regionalOfficeMap: { [key: string]: any[][] } = {};
  Logger.log(
    `支社ごとに行を分類中...（支社名は${REGIONAL_OFFICE_COL}列目にある想定です。）`,
  );
  planningList.forEach((row) => {
    const regionalOffice = row[REGIONAL_OFFICE_COL - 1];

    if (!regionalOffice) {
      return;
    }
    if (!regionalOfficeMap[regionalOffice]) {
      regionalOfficeMap[regionalOffice] = [];
    }

    regionalOfficeMap[regionalOffice].push(row.slice(0, BRANCH_OFFICE_COL));
  });
  Logger.log(
    `支社ごとの分類が完了しました。分類された支社数: ${Object.keys(regionalOfficeMap).length}`,
  );

  Object.keys(regionalOfficeMap).forEach((regionalOffice) => {
    const regionalOfficeSpreadsheetUrl =
      REGIONAL_OFFICE_SS_URL_MAP[regionalOffice] || null;

    // 現状「岐阜」、「0」、「#N/A」のいずれか
    if (!regionalOfficeSpreadsheetUrl) {
      Logger.log(
        `「${regionalOffice}」のスプレッドシートURLが見つかりません。`,
      );
      return;
    }

    const targetSheetName = `計画策定シート_${regionalOffice}`;

    Logger.log(`既存の「${targetSheetName}」を削除中...`);
    const targetSpreadsheet = SpreadsheetApp.openByUrl(
      regionalOfficeSpreadsheetUrl,
    );
    const oldSheet = targetSpreadsheet.getSheetByName(targetSheetName);
    if (oldSheet) {
      targetSpreadsheet.deleteSheet(oldSheet);
    }
    Logger.log(`削除完了。`);

    Logger.log(`計画策定シートをコピー中...`);
    const copiedSheet = planningSheet.copyTo(targetSpreadsheet);
    copiedSheet.setName(targetSheetName);
    Logger.log("コピー完了。");

    const regionalOfficeRecord = regionalOfficeMap[regionalOffice];

    const startRow = DATA_START_ROW + regionalOfficeRecord.length;
    const maxRows = copiedSheet.getMaxRows();
    if (maxRows >= startRow) {
      Logger.log(`コピーした計画策定シートから不要な行を削除中...`);

      const rowsToDelete = maxRows - startRow + 1;
      const safeRowsToDelete = Math.min(rowsToDelete, maxRows - startRow + 1);
      copiedSheet.deleteRows(startRow, safeRowsToDelete);

      Logger.log(`不要な行を ${safeRowsToDelete} 行削除しました。`);
    }

    Logger.log(
      `「${targetSheetName}」に${regionalOffice}の計画データをコピー中...`,
    );
    copiedSheet
      .getRange(
        DATA_START_ROW,
        1,
        regionalOfficeRecord.length,
        BRANCH_OFFICE_COL,
      )
      .setValues(regionalOfficeRecord);

    copiedSheet.insertRowAfter(startRow - 1);
    Logger.log(`計画のコピーが完了しました。`);
  });
}
