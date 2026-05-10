import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def _extract_title(item: dict) -> str:
    content = item.get("content", {})
    if isinstance(content, dict):
        return content.get("title", "")
    return item.get("title", "")


def _classify(score: float) -> str:
    if score >= 0.05:
        return "bullish"
    if score <= -0.05:
        return "bearish"
    return "neutral"


def get_sentiment(ticker: str):
    news_items = yf.Ticker(ticker).news or []

    headlines = []
    scores = []

    for item in news_items[:15]:
        title = _extract_title(item)
        if not title:
            continue
        compound = _analyzer.polarity_scores(title)["compound"]
        scores.append(compound)
        headlines.append({
            "headline": title,
            "sentiment": _classify(compound),
            "score": round(compound, 3),
        })

    if not headlines:
        return None

    avg = sum(scores) / len(scores)
    return {
        "overall_sentiment": _classify(avg),
        "avg_score": round(avg, 3),
        "articles_analyzed": len(headlines),
        "headlines": headlines,
    }
