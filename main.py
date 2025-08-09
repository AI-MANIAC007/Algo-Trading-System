import logging
from data_ingestion import fetch_data, save_to_csv
from trading_strategy import backtest_all
from predictor import train_model
from google_sheet.data_logger import update_sheet
from telegram_alerts import send_telegram
import pandas as pd
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TICKERS = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
DAYS = 180
CSV_PATH = "data/stock_data.csv"
BACKTEST_OUTPUT = "data/backtest_signals.csv"
TRADES_OUTPUT = "data/trades_log.csv"
SPREADSHEET_NAME = "Algo_Trading_Logs"   
GS_CREDS_PATH = "C:\\Users\\asus\\Downloads\\algo-trading-system-468317-e3ddb7efa99a.json"
ENABLE_GOOGLE_SHEETS = True
ENABLE_TELEGRAM = True
TELEGRAM_BOT_TOKEN = "7770021046:AAHHFJZXYRHJlzK7eQ_j_tA0pQi7bvq8lb8"
TELEGRAM_CHAT_ID = "6335855126"
ML_MODEL_SAVE = "models/model.joblib"  
# ----------------------------

def ensure_dirs():
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)

def run_pipeline():
    ensure_dirs()
    # 1) Data ingestion
    logger.info("Starting data ingestion...")
    df = fetch_data(TICKERS, days=DAYS)
    save_to_csv(df, CSV_PATH)

    # 2) Strategy backtest
    logger.info("Running backtest...")
    backtest_df, trades_df = backtest_all(csv_path=CSV_PATH)
    backtest_df.to_csv(BACKTEST_OUTPUT, index=False)
    trades_df.to_csv(TRADES_OUTPUT, index=False)
    logger.info("Backtest saved to %s and %s", BACKTEST_OUTPUT, TRADES_OUTPUT)

    # 3) ML model (per ticker) - demonstrate for each ticker, store results
    ml_summary = []
    for ticker in df["Ticker"].unique():
        logger.info("Training ML for %s", ticker)
        df_t = df[df["Ticker"] == ticker]
        try:
            res = train_model(df_t, model_type="tree", save_path=None)
            ml_summary.append({"Ticker": ticker, "Accuracy": res["accuracy"]})
            logger.info("Ticker %s ML accuracy: %.3f", ticker, res["accuracy"])
        except Exception as e:
            logger.exception("ML training failed for %s: %s", ticker, e)

    ml_summary_df = pd.DataFrame(ml_summary)

    # 4) Google Sheets
    if ENABLE_GOOGLE_SHEETS:
        logger.info("Uploading logs to Google Sheets...")
        df_for_sheet = backtest_df.copy()
        # Basic summary
        summary_df = df_for_sheet.groupby("Ticker").agg(
            Total_Strategy_Return=("Strategy_Return", "sum"),
            Trades=("Buy_Signal", "sum")
        ).reset_index()
        # Win ratio: simplistic calculation
        df_for_sheet["Win"] = df_for_sheet["Strategy_Return"] > 0
        win_df = df_for_sheet.groupby("Ticker")["Win"].mean().reset_index(name="Win_Ratio")

        df_dict = {
            "Trade_Log": df_for_sheet.tail(500),  # last 500 rows to keep small
            "Summary": summary_df,
            "Win_Ratio": win_df,
            "ML_Summary": ml_summary_df
        }
        update_sheet(SPREADSHEET_NAME, df_dict, GS_CREDS_PATH)

    # 5) Telegram alerts (optional) — send a daily summary
    if ENABLE_TELEGRAM:
        message = "Algo run complete.\n"
        for row in ml_summary:
            message += f"{row['Ticker']}: ML acc {row['Accuracy']:.2f}\n"
        if send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message):
            logger.info("Telegram summary sent.")

    logger.info("Pipeline finished.")

if __name__ == "__main__":
    run_pipeline()
