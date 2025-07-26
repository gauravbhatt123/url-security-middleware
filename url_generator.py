# url_generator.py
import random
import string
import base64
from urllib.parse import urlencode
from typing import Dict


class URLGenerator:
    SAFE_DOMAINS = [
        "example.com", "mytrustedsite.org", "shop.safe.net", "university.edu", "govservices.in"
    ]
    SAFE_PATHS = [
        "/home", "/about", "/products", "/services", "/contact", "/blog", "/news", "/dashboard"
    ]
    SAFE_QUERY_KEYS = ["utm_source", "ref", "id", "lang", "theme"]

    SUSPICIOUS_TLDS = [".ru", ".xyz", ".top", ".biz", ".click", ".gq", ".ml", ".tk"]
    SUSPICIOUS_DOMAINS = [
        "malware-download", "free-bitcoin", "get-rich-now", "ph1shing", "clickjack", "untrustedlogin"
    ]

    SQL_INJECTION_PAYLOADS = [
        "' OR 1=1 --", "'; DROP TABLE users; --", "' UNION SELECT password FROM users --"
    ]
    XSS_PAYLOADS = [
        "<script>alert(1)</script>", "<img src=x onerror=alert('XSS')>", "<svg/onload=alert(1)>"
    ]
    REDIRECTION_PAYLOADS = ["?redirect=http://evil.com", "?next=https://phish.com"]
    ENCODED_PAYLOADS = [
        base64.b64encode(b"<script>alert('hacked')</script>").decode()
    ]

    SCHEMES = ["http", "https"]

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

    def _random_query(self, keys: list) -> str:
        query: Dict[str, str] = {
            random.choice(keys): random.choice(["google", "newsletter", "42", "en", "dark"])
            for _ in range(random.randint(1, 3))
        }
        return f"?{urlencode(query)}"

    def generate_valid_url(self) -> str:
        scheme = "https"
        domain = random.choice(self.SAFE_DOMAINS)
        subdomain = random.choice(["", "www.", "api.", "shop.", "blog."])
        path = random.choice(self.SAFE_PATHS)
        query_string = self._random_query(self.SAFE_QUERY_KEYS)

        return f"{scheme}://{subdomain}{domain}{path}{query_string}"

    def generate_invalid_url(self) -> str:
        scheme = random.choice(self.SCHEMES)
        domain = (
            ".".join(str(random.randint(1, 255)) for _ in range(4))
            if random.random() < 0.33
            else f"{random.choice(self.SUSPICIOUS_DOMAINS)}{random.choice(self.SUSPICIOUS_TLDS)}"
        )
        subdomain = random.choice(["", "login.", "secure.", "click.", "verify.", "track."])
        path_base = random.choice(
            self.SQL_INJECTION_PAYLOADS + self.XSS_PAYLOADS + self.REDIRECTION_PAYLOADS + self.ENCODED_PAYLOADS
        )
        path = f"/{path_base.strip()}"

        # Add junk to path optionally
        if random.random() < 0.5:
            junk = "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 100)))
            path += f"/{junk}"

        # Suspicious query
        query = {
            random.choice(["q", "search", "input", "url"]): random.choice(
                self.SQL_INJECTION_PAYLOADS + self.XSS_PAYLOADS + self.ENCODED_PAYLOADS
            )
        }
        query_string = f"?{urlencode(query)}"

        return f"{scheme}://{subdomain}{domain}{path}{query_string}"


if __name__ == "__main__":
    gen = URLGenerator()

    print("🟢 Valid URLs:")
    for _ in range(5):
        print(gen.generate_valid_url())

    print("\n🔴 Invalid URLs:")
    for _ in range(5):
        print(gen.generate_invalid_url())
