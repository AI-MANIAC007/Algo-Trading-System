import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def authenticate_gsheet(creds_path):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    return gspread.authorize(creds)

def update_google_sheet(sheet_name, df_dict, creds_path):
    client = authenticate_gsheet(creds_path)
    try:
        sheet = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        sheet = client.create(sheet_name)

    for tab_name, df in df_dict.items():
        try:
            worksheet = sheet.worksheet(tab_name)
            sheet.del_worksheet(worksheet)
        except:
            pass

        worksheet = sheet.add_worksheet(title=tab_name, rows=str(len(df)+1), cols=str(len(df.columns)))
        df = df.copy()
        df = df.astype(str) 
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    print(f"Google Sheet '{sheet_name}' updated.")
