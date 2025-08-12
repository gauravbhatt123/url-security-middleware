#include "UrlSecurity.h"
#include <stdio.h>

int main() {
    printf("Testing URL Security Integration\n");
    printf("================================\n\n");
    
    // Test URLs
    const char *test_urls[] = {
        "https://www.google.com",
        "http://free-bitcoin.ru/get-rich-now",
        "https://secure-login.ph1sh.xyz/index.php?id=123",
        "http://malware-download.biz/<script>alert(1)</script>"
    };
    
    int num_tests = sizeof(test_urls) / sizeof(test_urls[0]);
    
    for (int i = 0; i < num_tests; i++) {
        printf("Test %d: %s\n", i + 1, test_urls[i]);
        
        url_security_result_t result;
        int ret = check_url_security(test_urls[i], &result);
        
        if (ret == 0) {
            printf("  Result: %s\n", result.is_safe ? "SAFE" : "MALICIOUS");
            printf("  Prediction: %s\n", result.prediction);
            printf("  Score: %.3f\n", result.score);
            if (result.explanation[0]) {
                printf("  Explanation: %s\n", result.explanation);
            }
        } else {
            printf("  Error: %s\n", result.error);
        }
        printf("\n");
    }
    
    return 0;
}
