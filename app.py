from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from data_fetcher import get_stock_data, get_current_price
from indicators import rsi, macd, bollinger_bands
from scorer import score_stock
from predictor import predict_price
from sentiment import get_sentiment
import cache

app = Flask(__name__)
CORS(app)


def get_close(ticker, period="3mo"):
    df = get_stock_data(ticker, period)
    if df is None:
        return None, None
    close = df["Close"].squeeze()
    return df, close


# ─── Routes ──────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "name": "Stock Insight API",
        "version": "1.0",
        "endpoints": [
            "/quote/<ticker>",
            "/indicators/<ticker>",
            "/score/<ticker>",
            "/compare?tickers=AAPL,MSFT",
            "/predict/<ticker>?days=7",
            "/sentiment/<ticker>"
        ]
    })


@app.route("/quote/<ticker>")
def quote(ticker):
    ticker = ticker.upper()
    cached = cache.get(ticker + "_quote")
    if cached:
        return jsonify(cached)

    df, close = get_close(ticker)
    if close is None:
        return jsonify({"error": f"No data found for {ticker}"}), 404

    result = {
        "ticker": ticker,
        "price": round(float(close.iloc[-1]), 2),
        "open": round(float(df["Open"].iloc[-1]), 2),
        "high": round(float(df["High"].iloc[-1]), 2),
        "low": round(float(df["Low"].iloc[-1]), 2),
        "volume": int(df["Volume"].iloc[-1]),
        "change_pct": round(
            float((close.iloc[-1] / close.iloc[-2] - 1) * 100), 2
        ),
        "cached": False
    }

    cache.set(ticker + "_quote", result, ttl=60)
    return jsonify(result)


@app.route("/indicators/<ticker>")
def indicators_route(ticker):
    ticker = ticker.upper()
    cached = cache.get(ticker + "_ind")
    if cached:
        return jsonify(cached)

    df, close = get_close(ticker)
    if close is None:
        return jsonify({"error": f"No data found for {ticker}"}), 404

    rsi_series = rsi(close)
    macd_line, signal_line, histogram = macd(close)
    upper, middle, lower = bollinger_bands(close)

    result = {
        "ticker": ticker,
        "rsi": round(float(rsi_series.iloc[-1]), 2),
        "macd": {
            "macd_line": round(float(macd_line.iloc[-1]), 4),
            "signal_line": round(float(signal_line.iloc[-1]), 4),
            "histogram": round(float(histogram.iloc[-1]), 4)
        },
        "bollinger_bands": {
            "upper": round(float(upper.iloc[-1]), 2),
            "middle": round(float(middle.iloc[-1]), 2),
            "lower": round(float(lower.iloc[-1]), 2)
        }
    }

    cache.set(ticker + "_ind", result, ttl=300)
    return jsonify(result)


@app.route("/score/<ticker>")
def score_route(ticker):
    ticker = ticker.upper()
    cached = cache.get(ticker + "_score")
    if cached:
        return jsonify(cached)

    df, close = get_close(ticker)
    if close is None:
        return jsonify({"error": f"No data found for {ticker}"}), 404

    rsi_val = float(rsi(close).iloc[-1])
    macd_line, signal_line, _ = macd(close)
    upper, _, lower_bb = bollinger_bands(close)
    price = float(close.iloc[-1])

    scored = score_stock(
        rsi_val,
        float(macd_line.iloc[-1]),
        float(signal_line.iloc[-1]),
        price,
        float(upper.iloc[-1]),
        float(lower_bb.iloc[-1])
    )

    scored["ticker"] = ticker
    scored["price"] = round(price, 2)
    scored["rsi"] = round(rsi_val, 2)

    cache.set(ticker + "_score", scored, ttl=300)
    return jsonify(scored)


@app.route("/compare")
def compare():
    raw = request.args.get("tickers", "AAPL,MSFT,GOOGL")
    tickers = [t.strip().upper() for t in raw.split(",")][:5]

    results = []
    for t in tickers:
        df, close = get_close(t)
        if close is None:
            continue

        rsi_val = float(rsi(close).iloc[-1])
        macd_line, signal_line, _ = macd(close)
        upper, _, lower_bb = bollinger_bands(close)
        price = float(close.iloc[-1])

        scored = score_stock(
            rsi_val,
            float(macd_line.iloc[-1]),
            float(signal_line.iloc[-1]),
            price,
            float(upper.iloc[-1]),
            float(lower_bb.iloc[-1])
        )

        results.append({
            "ticker": t,
            "price": round(price, 2),
            "rsi": round(rsi_val, 2),
            "signal": scored["signal"],
            "score": scored["score"]
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(results)


@app.route("/predict/<ticker>")
def predict(ticker):
    ticker = ticker.upper()
    days = min(max(request.args.get("days", 7, type=int), 1), 30)

    cache_key = f"{ticker}_predict_{days}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)

    forecast = predict_price(ticker, days)
    if forecast is None:
        return jsonify({"error": f"No data found for {ticker}"}), 404

    result = {"ticker": ticker, "forecast_days": days, "forecast": forecast}
    cache.set(cache_key, result, ttl=3600)
    return jsonify(result)


@app.route("/sentiment/<ticker>")
def sentiment_route(ticker):
    ticker = ticker.upper()
    cached = cache.get(ticker + "_sentiment")
    if cached:
        return jsonify(cached)

    data = get_sentiment(ticker)
    if data is None:
        return jsonify({"error": f"No news found for {ticker}"}), 404

    data["ticker"] = ticker
    cache.set(ticker + "_sentiment", data, ttl=1800)
    return jsonify(data)


# ─── Dashboard Route ─────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ─── Run App ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)