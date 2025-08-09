import logging
from data_ingestion import fetch_data, save_to_csv
from trading_strategy import backtest_all
from predictor import train_and_evaluate_model
from google_sheet.data_logger import update_google_sheet
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
    backtest_df= backtest_all(csv_file_path=CSV_PATH)
    backtest_df.to_csv(BACKTEST_OUTPUT, index=False)
    logger.info("Backtest saved to %s", BACKTEST_OUTPUT)

    # 3) ML model (per ticker) - demonstrate for each ticker, store results
    ml_summary = []
    tickers = [col.replace("Close_", "") for col in df.columns if col.startswith("Close_")]

    for ticker in tickers:
        logger.info("Training ML for %s", ticker)
        df_t = pd.DataFrame({
            "Close": df[f"Close_{ticker}"],
            "Volume": df[f"Volume_{ticker}"]
        })
        try:
            acc, cm,model = train_and_evaluate_model(df_t)
            ml_summary.append({"Ticker": ticker, "Accuracy": acc})
            logger.info("Ticker %s ML accuracy: %.3f", ticker, acc)
        except Exception as e:
            logger.exception("ML training failed for %s: %s", ticker, e)

    ml_summary_df = pd.DataFrame(ml_summary)

  # 4) Google Sheets
    if ENABLE_GOOGLE_SHEETS:
        logger.info("Uploading logs to Google Sheets...")
        df_for_sheet = backtest_df.copy()
        
        # Reset index to avoid duplicate labels problem
        df_for_sheet = df_for_sheet.reset_index(drop=True)
        
        if "Sell_Price" in df_for_sheet.columns and "Buy_Price" in df_for_sheet.columns:

            df_for_sheet["Last_Buy_Price"] = df_for_sheet["Buy_Price"].ffill()
            df_for_sheet["P&L"] = 0.0

            sell_mask = df_for_sheet["Sell_Signal"] == True
            df_for_sheet.loc[sell_mask, "P&L"] = (
                df_for_sheet.loc[sell_mask, "Sell_Price"].fillna(0) - 
                df_for_sheet.loc[sell_mask, "Last_Buy_Price"].fillna(0)
            ) * df_for_sheet.get("Quantity", 1)

            buy_mask = df_for_sheet["Buy_Signal"] == True
            prev_buy_price = df_for_sheet["Last_Buy_Price"].shift(1)
            df_for_sheet.loc[buy_mask, "P&L"] = (
                df_for_sheet.loc[buy_mask, "Buy_Price"].fillna(0) - 
                prev_buy_price.fillna(0)
            ) * df_for_sheet.get("Quantity", 1)

        else:
            df_for_sheet["P&L"] = df_for_sheet["Strategy_Return"] * 100

    # Rest of your code for summary, win ratio, and Google Sheets upload follows...

        # Summary table
        summary_df = df_for_sheet.groupby("Ticker").agg(
            Total_PnL=("P&L", "sum"),
            Total_Strategy_Return=("Strategy_Return", "sum"),
            Trades=("Buy_Signal", "sum")
        ).reset_index()

        # Win ratio
        df_for_sheet["Win"] = df_for_sheet["P&L"] > 0
        win_df = df_for_sheet.groupby("Ticker")["Win"].mean().reset_index(name="Win_Ratio")

        # Send to Google Sheets
        df_dict = {
            "Trade_Log": df_for_sheet.tail(500),
            "Summary": summary_df,
            "Win_Ratio": win_df,
        }
        update_google_sheet(SPREADSHEET_NAME, df_dict, GS_CREDS_PATH)

    # 5) Telegram alerts (optional) — send a daily summary
    if ENABLE_TELEGRAM:
        for _, row in backtest_df.iterrows():
            date_str = str(row.get("Date", ""))
            ticker = row.get("Ticker", "")
            
            # BUY ALERT
            if row.get("Buy_Signal", False) == 1:
                msg = f"📈 BUY Signal\nTicker: {ticker}\nDate: {date_str}\nPrice: {row.get('Buy_Price', 'N/A')}"
                send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
            
            # SELL ALERT
            if row.get("Sell_Signal", False) == 1:
                msg = f"📉 SELL Signal\nTicker: {ticker}\nDate: {date_str}\nPrice: {row.get('Sell_Price', 'N/A')}"
                if "P&L" in row:
                    msg += f"\nP&L: {row['P&L']:.2f}"
                send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)

        # --- Daily Summary ---
        message = "✅ Algo run complete.\n"
        for row in ml_summary:
            message += f"{row['Ticker']}: ML acc {row['Accuracy']:.2f}\n"
        if send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message):
            logger.info("Telegram summary sent.")

    logger.info("Pipeline finished.")

if __name__ == "__main__":
    run_pipeline()
