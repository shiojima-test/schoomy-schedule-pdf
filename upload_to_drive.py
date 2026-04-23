"""Google Drive にPDFをアップロード（既存ファイルがあれば置き換え）。

認証: 環境変数 GOOGLE_SERVICE_ACCOUNT_JSON に
サービスアカウントJSONキーの文字列を丸ごとセット。

使用例:
    export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account-key.json)"
    python upload_to_drive.py test.pdf
"""
import json
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = '12caVEED6ZAF_g30o3ZWmI67GA3g9aFvz'
PDF_NAME = 'スクーミーフェスタ年間スケジュール_2026年度.pdf'


def upload_pdf(local_path, credentials_json_str):
    creds_info = json.loads(credentials_json_str)
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES)
    drive = build('drive', 'v3', credentials=creds)

    query = f"name='{PDF_NAME}' and '{FOLDER_ID}' in parents and trashed=false"
    existing = drive.files().list(
        q=query, fields='files(id, name)',
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute().get('files', [])

    media = MediaFileUpload(local_path, mimetype='application/pdf', resumable=False)

    if existing:
        file_id = existing[0]['id']
        file = drive.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True,
        ).execute()
        print(f'既存ファイル上書き: {file_id}')
    else:
        metadata = {'name': PDF_NAME, 'parents': [FOLDER_ID]}
        file = drive.files().create(
            body=metadata, media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True,
        ).execute()
        print(f'新規作成: {file["id"]}')

    try:
        drive.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'},
            supportsAllDrives=True,
        ).execute()
    except Exception as e:
        print(f'warn: could not update permission (already public?): {e}')

    print(f'Uploaded: {file["webViewLink"]}')
    return file['id']


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python upload_to_drive.py <pdf_path>', file=sys.stderr)
        sys.exit(2)
    creds = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not creds:
        print('ERROR: GOOGLE_SERVICE_ACCOUNT_JSON env var is required', file=sys.stderr)
        sys.exit(1)
    upload_pdf(sys.argv[1], creds)
