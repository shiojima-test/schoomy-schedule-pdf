/**
 * スクーミーフェスタ年間スケジュール PDF 更新トリガー
 *
 * 使い方:
 *   1. スプレッドシートを開き「拡張機能」→「Apps Script」
 *   2. このコード全文を貼り付けて保存
 *   3. シートに戻り再読み込み
 *   4. メニュー「📄 PDF操作」→「① PDFを生成・更新」
 *   5. 初回のみ UrlFetch へのアクセス許可を承認
 */

const GITHUB_OWNER = 'shiojima-test';
const GITHUB_REPO = 'schoomy-schedule-pdf';
const GITHUB_TOKEN = 'PASTE_YOUR_GITHUB_TOKEN_HERE';  // 貼り付け時に実トークンに差し替える
const DRIVE_FOLDER_URL = 'https://drive.google.com/drive/folders/12caVEED6ZAF_g30o3ZWmI67GA3g9aFvz';
const PDF_DIRECT_URL = 'https://drive.google.com/uc?export=download&id=11MbcUecXNnd1bCroHQr5s117FpouooRj';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('📄 PDF操作')
    .addItem('① PDFを生成・更新', 'triggerPdfGeneration')
    .addItem('② ダウンロードURLを表示', 'showDownloadUrl')
    .addItem('③ Driveフォルダを開く', 'openDriveFolder')
    .addToUi();
}

function triggerPdfGeneration() {
  const ui = SpreadsheetApp.getUi();
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/dispatches`;

  try {
    const response = UrlFetchApp.fetch(url, {
      method: 'post',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github+json',
      },
      contentType: 'application/json',
      payload: JSON.stringify({ event_type: 'generate-pdf' }),
      muteHttpExceptions: true,
    });

    const code = response.getResponseCode();
    if (code === 204) {
      ui.alert(
        '✅ PDF生成を開始しました',
        '1-2分後に Google Drive フォルダに最新PDFが作成されます。\n\n' +
        'ダウンロードURL（SWELL用・変わりません）:\n' + PDF_DIRECT_URL,
        ui.ButtonSet.OK
      );
    } else {
      ui.alert('❌ エラー (HTTP ' + code + ')', response.getContentText(), ui.ButtonSet.OK);
    }
  } catch (e) {
    ui.alert('❌ エラー', e.toString(), ui.ButtonSet.OK);
  }
}

function showDownloadUrl() {
  SpreadsheetApp.getUi().alert(
    'SWELL に貼るダウンロードURL',
    PDF_DIRECT_URL + '\n\n※このURLは固定なので、PDFを更新してもリンクは変わりません。',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

function openDriveFolder() {
  SpreadsheetApp.getUi().alert(
    'Google Drive フォルダ',
    DRIVE_FOLDER_URL,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}
