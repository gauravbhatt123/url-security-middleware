#!/usr/bin/env python3
"""
URL Security Checker - Standalone script for C integration
This script can be called as a subprocess from C code
"""

import sys
import json
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from predict_url import predict_url
    MALWARE_DETECTION_AVAILABLE = True
except ImportError as e:
    MALWARE_DETECTION_AVAILABLE = False
    print("ERROR: Malware detection not available")
    print("RESULT: 0")
    print("PREDICTION: unknown")
    print("SCORE: 0")
    sys.exit(1)

def check_url(url):
    """Check URL and return simple format result"""
    try:
        result = predict_url(url)
        print(f"URL: {url}")
        print(f"PREDICTION: {result['prediction']}")
        print(f"SCORE: {result['score']}")
        print(f"RESULT: {result['result']}")
        if result.get('explanation'):
            print(f"EXPLANATION: {result['explanation']}")
        print("SUCCESS: true")
        return result['result']
    except Exception as e:
        print(f"URL: {url}")
        print(f"ERROR: {str(e)}")
        print("RESULT: 0")
        print("SUCCESS: false")
        return 0

def main():
    if len(sys.argv) != 2:
        print("ERROR: Usage: python3 url_checker.py <url>")
        print("RESULT: 0")
        sys.exit(1)
    
    url = sys.argv[1]
    result_value = check_url(url)
    
    # Exit with code 0 for safe URLs, 1 for malicious
    if result_value == 1:
        sys.exit(1)  # Malicious URL
    else:
        sys.exit(0)  # Safe URL

if __name__ == "__main__":
    main()
