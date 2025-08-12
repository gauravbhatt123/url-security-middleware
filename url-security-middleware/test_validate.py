#!/usr/bin/env python3

from url_validator import validate_url

# Test the validate_url function
test_urls = [
    "https://www.google.com",
    "http://example.com/login",
    "https://github.com"
]

print("Testing validate_url function:")
for url in test_urls:
    try:
        result = validate_url(url)
        print(f"URL: {url}")
        print(f"Result: {result}")
        print("-" * 50)
    except Exception as e:
        print(f"Error with {url}: {e}")
        print("-" * 50) 