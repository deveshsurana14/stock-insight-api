def score_stock(rsi_val, macd_val, signal_val, price, upper_bb, lower_bb):
    score = 0
    reasons = []

    if rsi_val < 30:
        score += 2
        reasons.append("RSI oversold — potential bounce")
    elif rsi_val > 70:
        score -= 2
        reasons.append("RSI overbought — potential pullback")
    else:
        reasons.append(f"RSI neutral at {round(rsi_val, 1)}")

    if macd_val > signal_val:
        score += 1
        reasons.append("MACD bullish crossover")
    else:
        score -= 1
        reasons.append("MACD bearish — momentum declining")

    if price < lower_bb:
        score += 1
        reasons.append("Price below lower Bollinger Band — oversold zone")
    elif price > upper_bb:
        score -= 1
        reasons.append("Price above upper Bollinger Band — overbought zone")
    else:
        reasons.append("Price within Bollinger Bands")

    if score >= 3:
        signal = "STRONG BUY"
    elif score >= 1:
        signal = "BUY"
    elif score <= -3:
        signal = "STRONG SELL"
    elif score <= -1:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "score": score,
        "signal": signal,
        "reasons": reasons
    }