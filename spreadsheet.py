import google.auth
import gspread

# from google.oauth2.service_account import Credentials

def spreadsheet_test_read():
    scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    ]

    credentials, _ = google.auth.default(scopes=scopes)

    client = gspread.authorize(credentials)

    # スプレッドシートID（URLの一部）
    spreadsheet_id = "1N33W_VZptLOlu1-tlGliSvJVDFAV3Sh1cN192A-UN5o"

    # スプレッドシートを開く
    spreadsheet = client.open_by_key(spreadsheet_id)

    worksheet = spreadsheet.sheet1

    data = worksheet.get_all_values()

    print(data)
