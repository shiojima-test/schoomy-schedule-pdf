> **このリポジトリはスクーミー社内の中央ハブから管理されています。**
> 仕様詳細・運用フロー・修正手順については、社内ドキュメントを参照してください。

---

# schoomy-schedule-pdf

スクーミーフェスタ年間スケジュール PDF 自動生成システム。
スプレッドシート更新 → シート上のボタン押下 → GitHub Actions → Python(reportlab)でA4横PDF生成 → Google Drive自動アップロード。

## 構成

| レイヤー | 役割 |
| --- | --- |
| Google スプレッドシート | データ入力元 / GAS ボタンで発火 |
| GAS (`gas_trigger.gs`) | `/dispatches` で GitHub Actions を起動 |
| GitHub Actions (`.github/workflows/generate-pdf.yml`) | version.txt を +1 / PDF 生成 / Drive にアップロード |
| `generate_pdf.py` | CSV 取得 → reportlab で A4横 PDF 生成（Noto Sans JP 使用） |
| `upload_to_drive.py` | サービスアカウントで Drive フォルダに upload（update-or-create） |

## データソース

- 公開 CSV: <https://docs.google.com/spreadsheets/d/e/2PACX-1vRooWpJWGHr60e039XzbxEbeZ7p6zEL-wuP-xrq4jv1TnZXHSOWjtT8FvScuKsQn05aZx8PfIW14d83/pub?output=csv>
- 出力 Drive フォルダ: <https://drive.google.com/drive/folders/12caVEED6ZAF_g30o3ZWmI67GA3g9aFvz>
- 固定 PDF 直URL (SWELL用): `https://drive.google.com/uc?export=download&id=11MbcUecXNnd1bCroHQr5s117FpouooRj`

## ローカル実行

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate_pdf.py --version 1 --update-date 2026-04-24 --output test.pdf
open test.pdf
```

Drive アップロードを試す場合:

```bash
export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account-key.json)"
.venv/bin/python upload_to_drive.py test.pdf
```

## GAS（スプレッドシート側ボタン）設置手順

1. スプレッドシート `15YQZzEluBNixD-ct8bIG4bb4Dlptzb2adCbuLXBQ8Pc` を開く
2. 「拡張機能」→「Apps Script」
3. `gas_trigger.gs` の中身を全文貼り付けて保存
   - **重要**: `const GITHUB_TOKEN = 'PASTE_YOUR_GITHUB_TOKEN_HERE';` の部分を実トークンに差し替える
   - パブリックリポジトリにトークンを直書きしないためのプレースホルダ。GAS は非公開なので貼り付けてOK
4. スプレッドシートに戻ってブラウザ再読み込み
5. メニューバーに「📄 PDF操作」が出現
6. 「① PDFを生成・更新」をクリック
7. 初回のみ UrlFetch へのアクセス許可を承認
8. 完了ダイアログが出たら、1-2分後にDriveフォルダのPDFが更新される

## SWELL ダウンロードボタン

以下のURLを SWELL のボタンに設定:

```
https://drive.google.com/uc?export=download&id=11MbcUecXNnd1bCroHQr5s117FpouooRj
```

このURLは固定なので PDF を更新してもリンクは変わりません。
