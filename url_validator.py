# url_validator.py
from predict_url import predict_url

def validate_url(url: str):
    # Convert HttpUrl object to string if needed
    if hasattr(url, '__str__'):
        url = str(url)
    
    prediction, score = predict_url(url)

    category = "SAFE" if prediction == "benign" else "DANGEROUS"
    reasons = [f"Predicted as {prediction.upper()} by CNN-LSTM model"]

    # Convert numpy types to Python native types for JSON serialization
    if hasattr(score, 'item'):
        score = float(score.item())
    else:
        score = float(score)

    return {
        "url": url,
        "score": round(score, 2),
        "category": category,
        "reasons": reasons
    }
