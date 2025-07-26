import re
import socket
import string
import tldextract
from urllib.parse import urlparse, parse_qs
from math import log2


# Suspicious patterns
SQL_INJECTION_PATTERNS = [
    r"(\%27)|(')|(--)", r"(\%3D)|(=)", r"(\%3B)|(;)", r"(OR\s+1=1)", r"(UNION\s+SELECT)", r"(DROP\s+TABLE)"
]

XSS_PATTERNS = [
    r"<script.*?>.*?</script.*?>", r"<.*?onerror=.*?>", r"<svg.*?onload=.*?>",
    r"(document\.cookie)", r"(alert\s*\()"
]

ENCODED_PAYLOAD_PATTERNS = [r"(base64,)", r"(data:text/html)", r"(eval\(.*\))"]

SUSPICIOUS_TLDS = [".ru", ".xyz", ".top", ".biz", ".click", ".gq", ".ml", ".tk", ".zip", ".country"]
TRUSTED_TLDS = [".com", ".org", ".net", ".edu", ".gov", ".in", ".co"]

COMMON_MALICIOUS_KEYWORDS = ["login", "secure", "verify", "update", "banking", "paypal", "free", "bitcoin", "click"]

SUSPICIOUS_DOMAINS = ["ph1sh", "cl1ck", "0auth", "secure-login", "getrich", "malware", "update-your-password"]


def calculate_entropy(text):
    if not text:
        return 0
    prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
    return -sum([p * log2(p) for p in prob])


def is_ip_address(domain):
    try:
        socket.inet_aton(domain)
        return True
    except socket.error:
        return False


def validate_url(url):
    score = 1.0
    reasons = []

    parsed = urlparse(url)

    # 1. Scheme check
    if parsed.scheme != "https":
        score -= 0.1
        reasons.append("Insecure scheme (not HTTPS)")

    # 2. Domain and TLD analysis
    domain_info = tldextract.extract(parsed.netloc)
    full_domain = f"{domain_info.subdomain}.{domain_info.domain}.{domain_info.suffix}".strip(".")
    tld = f".{domain_info.suffix}"

    if is_ip_address(parsed.hostname or ""):
        score -= 0.3
        reasons.append("IP address used instead of domain")

    if tld in SUSPICIOUS_TLDS:
        score -= 0.2
        reasons.append(f"Suspicious top-level domain: {tld}")

    if any(kw in full_domain for kw in SUSPICIOUS_DOMAINS):
        score -= 0.2
        reasons.append("Suspicious domain name pattern")

    # 3. Path inspection
    path = parsed.path.lower()
    for pattern in SQL_INJECTION_PATTERNS + XSS_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            score -= 0.2
            reasons.append(f"Suspicious path pattern matched: {pattern}")
            break

    if len(path) > 100:
        score -= 0.1
        reasons.append("Path is unusually long")

    if calculate_entropy(path) > 4.5:
        score -= 0.1
        reasons.append("High entropy path (possible obfuscation)")

    # 4. Query string analysis
    query = parse_qs(parsed.query)
    for key, values in query.items():
        full = f"{key}={' '.join(values)}"
        for pattern in SQL_INJECTION_PATTERNS + XSS_PATTERNS + ENCODED_PAYLOAD_PATTERNS:
            if re.search(pattern, full, re.IGNORECASE):
                score -= 0.2
                reasons.append(f"Suspicious query pattern: {pattern}")
                break

        if any(k in key.lower() for k in ["redirect", "url", "next"]):
            for val in values:
                if any(bad in val for bad in SUSPICIOUS_DOMAINS):
                    score -= 0.2
                    reasons.append("Suspicious redirection in query")

    # 5. Overall URL structure
    if len(url) > 200:
        score -= 0.1
        reasons.append("Very long URL")

    if calculate_entropy(url) > 4.5:
        score -= 0.1
        reasons.append("High entropy URL")

    if url.count("//") > 2:
        score -= 0.05
        reasons.append("Multiple redirect-like segments (//)")

    # Final sanitize
    score = round(max(min(score, 1.0), 0.0), 2)
    if score >= 0.85:
        category = "SAFE"
    elif score >= 0.6:
        category = "MODERATE RISK"
    else:
        category = "DANGEROUS"

    return {
        "url": url,
        "score": score,
        "category": category,
        "reasons": reasons
    }


# Example testing
if __name__ == "__main__":
    test_urls = [
        "https://example.com/login?user=admin",
        "http://192.168.1.1/admin",
        "https://ph1shing.biz/<script>alert('x')</script>",
        "https://secure-login.xyz?redirect=http://evil.com",
        "https://mytrustedsite.org/blog?id=42&utm_source=newsletter"
    ]

    for url in test_urls:
        result = validate_url(url)
        print(f"\n🔍 {result['url']}\n→ Score: {result['score']} | Category: {result['category']}\nReasons: {result['reasons']}")


