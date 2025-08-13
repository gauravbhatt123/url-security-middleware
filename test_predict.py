#!/usr/bin/env python3

from predict_url import predict_url

# Test the predict_url function
test_urls = [
    "https://www.google.com",
    "http://example.com/login",
    "https://github.com"
]

print("Testing predict_url function:")
for url in test_urls:
    try:
        prediction, confidence = predict_url(url)
        print(f"URL: {url}")
        print(f"Prediction: {prediction}")
        print(f"Confidence: {confidence}")
        print("-" * 50)
    except Exception as e:
        print(f"Error with {url}: {e}")
        print("-" * 50) 