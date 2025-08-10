from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    score = analyzer.polarity_scores(text)
    compound = score["compound"]
    if compound >= 0.05:
        mood = "positive"
    elif compound <= -0.05:
        mood = "negative"
    else:
        mood = "neutral"
    return {"score": compound, "mood": mood}
