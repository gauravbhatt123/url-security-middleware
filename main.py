# main.py
from url_generator import URLGenerator
from url_validator import validate_url
from typing import Dict


class URLSecurityAnalyzer:
    def __init__(self):
        self.generator = URLGenerator()

    def print_result(self, result: Dict):
        print(f"\n🔎 URL: {result['url']}")
        print(f"→ Score: {result['score']}")
        print(f"→ Category: {result['category']}")
        if result["reasons"]:
            print("⚠️ Reasons:")
            for reason in result["reasons"]:
                print(f"  - {reason}")
        else:
            print("✅ No issues detected.")

    def test_valid_urls(self, count: int = 3):
        print("\n🟢 Testing VALID URLs:")
        for _ in range(count):
            url = self.generator.generate_valid_url()
            result = validate_url(url)  # ✅ Correct usage
            self.print_result(result)

    def test_invalid_urls(self, count: int = 3):
        print("\n🔴 Testing INVALID URLs:")
        for _ in range(count):
            url = self.generator.generate_invalid_url()
            result = validate_url(url)  # ✅ Correct usage
            self.print_result(result)

    def test_custom_urls(self):
        print("\n💬 Test your own URLs (press enter to skip):")
        while True:
            try:
                custom_url = input("Enter a URL to test (or press Enter to go back): ").strip()
                if not custom_url:
                    break
                result = validate_url(custom_url)  # ✅ Correct usage
                self.print_result(result)
            except KeyboardInterrupt:
                print("\n⛔ Interrupted by user.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def run(self):
        print("🚀 URL Security Analyzer")
        while True:
            print("\nSelect an option:")
            print("1. Test generated VALID URLs")
            print("2. Test generated INVALID URLs")
            print("3. Test CUSTOM URLs")
            print("4. Exit")

            choice = input("Enter your choice (1/2/3/4): ").strip()

            if choice == "1":
                self.test_valid_urls()
            elif choice == "2":
                self.test_invalid_urls()
            elif choice == "3":
                self.test_custom_urls()
            elif choice == "4":
                print("👋 Exiting. Stay safe online!")
                break
            else:
                print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    analyzer = URLSecurityAnalyzer()
    analyzer.run()
