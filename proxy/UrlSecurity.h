#ifndef URL_SECURITY_H
#define URL_SECURITY_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/stat.h>

// Structure to hold URL security check result
typedef struct {
    int is_safe;           // 1 if safe, 0 if malicious
    char prediction[64];   // Prediction class
    double score;          // Confidence score
    char explanation[256]; // Explanation
    char error[256];       // Error message if any
} url_security_result_t;

// Function prototypes
int check_url_security(const char *url, url_security_result_t *result);
void log_url_check(const char *url, const url_security_result_t *result);
char* get_block_page_html(const char *reason);

// Configuration
#define URL_CHECKER_PATH "../url-security-middleware/url_checker.py"
#define MAX_URL_LENGTH 2048
#define MAX_CMD_LENGTH 4096

#endif // URL_SECURITY_H
