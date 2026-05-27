function doGet() {
  const dbtDocsFileId = "1Jz8pxRT4orbitJz6f4oB5g1t6m6jz1uU";

  const dbtDocsFile = DriveApp.getFileById(dbtDocsFileId);
  const htmlContent = dbtDocsFile.getBlob().getDataAsString();

  return HtmlService.createHtmlOutput(htmlContent)
    .addMetaTag("viewport", "width=device-width, initial-scale=1")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
