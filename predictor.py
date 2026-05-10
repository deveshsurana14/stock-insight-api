import pandas as pd
from prophet import Prophet
from data_fetcher import get_stock_data


def predict_price(ticker: str, days: int = 7):
    df = get_stock_data(ticker, period="1y")
    if df is None:
        return None

    close = df["Close"].squeeze()
    ds_col = df.index if df.index.tz is None else df.index.tz_convert(None)

    cap = float(close.max()) * 1.5
    prophet_df = pd.DataFrame({
        "ds": ds_col,
        "y": close.values,
        "floor": 0.0,
        "cap": cap,
    })

    model = Prophet(
        growth="logistic",
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.01,
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=days, freq="B")
    future["floor"] = 0.0
    future["cap"] = cap
    forecast = model.predict(future)

    result = []
    for _, row in forecast.tail(days).iterrows():
        result.append({
            "date": row["ds"].strftime("%Y-%m-%d"),
            "predicted_price": round(float(row["yhat"]), 2),
            "lower_bound": round(float(row["yhat_lower"]), 2),
            "upper_bound": round(float(row["yhat_upper"]), 2),
        })

    return result
