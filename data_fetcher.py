import yfinance as yf
import pandas as pd

def get_stock_data(ticker: str, period: str = "3mo"):
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return None

def get_current_price(ticker: str):
    try:
        t = yf.Ticker(ticker)
        return round(t.fast_info["last_price"], 2)
    except Exception:
        return None