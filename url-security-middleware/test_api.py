#!/usr/bin/env python3

import requests
import json

# Test the API endpoints
base_url = "http://localhost:8000"

def test_logs():
    """Test the logs endpoint"""
    try:
        response = requests.get(f"{base_url}/logs")
        print(f"Logs endpoint status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error testing logs: {e}")

def test_check_url():
    """Test the check-url endpoint"""
    try:
        data = {"url": "https://www.google.com"}
        response = requests.post(f"{base_url}/check-url", json=data)
        print(f"Check URL endpoint status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error testing check-url: {e}")

if __name__ == "__main__":
    print("Testing API endpoints...")
    test_logs()
    print("-" * 50)
    test_check_url() 