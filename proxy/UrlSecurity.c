#include "UrlSecurity.h"
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <ctype.h>
#include <time.h>

// Simple value extraction using grep-like approach
static int extract_value(const char *output, const char *key, char *value_buffer, size_t buffer_size) {
    char search_pattern[128];
    snprintf(search_pattern, sizeof(search_pattern), "%s: ", key);
    
    const char *line_start = output;
    const char *line_end;
    
    while (*line_start) {
        // Find end of current line
        line_end = strchr(line_start, '\n');
        if (!line_end) line_end = line_start + strlen(line_start);
        
        // Check if this line starts with our key (exact match)
        if (strncmp(line_start, search_pattern, strlen(search_pattern)) == 0) {
            // Found the key, extract the value
            const char *value_start = line_start + strlen(search_pattern);
            int i = 0;
            while (value_start < line_end && i < buffer_size - 1) {
                value_buffer[i] = *value_start;
                i++;
                value_start++;
            }
            value_buffer[i] = '\0';
            return 1; // Success
        }
        
        // Move to next line
        if (*line_end == '\n') {
            line_start = line_end + 1;
        } else {
            break; // End of string
        }
    }
    
    return 0; // Not found
}

// Check if URL is safe by calling Python model
int check_url_security(const char *url, url_security_result_t *result) {
    if (!url || !result) {
        return -1;
    }
    
    // Initialize result structure
    memset(result, 0, sizeof(url_security_result_t));
    result->is_safe = 1; // Default to safe
    
    // Check if Python script exists
    struct stat st;
    if (stat(URL_CHECKER_PATH, &st) != 0) {
        strcpy(result->error, "URL checker script not found");
        return -1;
    }
    
    // Build command with virtual environment activation
    char cmd[MAX_CMD_LENGTH];
    snprintf(cmd, sizeof(cmd), "cd ../url-security-middleware && ./venv/bin/python3 url_checker.py \"%s\"", url);
    
    // Execute command and capture output
    FILE *pipe = popen(cmd, "r");
    if (!pipe) {
        strcpy(result->error, "Failed to execute URL checker");
        return -1;
    }
    
    char buffer[1024];
    char output[2048] = "";
    size_t total_len = 0;
    
    // Read output
    while (fgets(buffer, sizeof(buffer), pipe) != NULL) {
        size_t len = strlen(buffer);
        if (total_len + len < sizeof(output)) {
            strcat(output, buffer);
            total_len += len;
        }
    }
    
    int status = pclose(pipe);
    
    // Parse output using simple extraction
    char result_buffer[64];
    char prediction_buffer[64];
    char score_buffer[64];
    char explanation_buffer[256];
    char error_buffer[256];
    
    int result_found = extract_value(output, "RESULT", result_buffer, sizeof(result_buffer));
    int prediction_found = extract_value(output, "PREDICTION", prediction_buffer, sizeof(prediction_buffer));
    int score_found = extract_value(output, "SCORE", score_buffer, sizeof(score_buffer));
    int explanation_found = extract_value(output, "EXPLANATION", explanation_buffer, sizeof(explanation_buffer));
    int error_found = extract_value(output, "ERROR", error_buffer, sizeof(error_buffer));
    
    printf("[DEBUG] Raw output: %s\n", output);
    printf("[DEBUG] Parsed values - result: %s, prediction: %s, score: %s\n", 
           result_found ? result_buffer : "NULL", 
           prediction_found ? prediction_buffer : "NULL", 
           score_found ? score_buffer : "NULL");
    
    if (result_found && strlen(result_buffer) > 0) {
        int result_value = atoi(result_buffer);
        result->is_safe = (result_value == 0);
        printf("[DEBUG] Result value: %s -> %d, is_safe: %d\n", result_buffer, result_value, result->is_safe);
    }
    
    if (prediction_found && strlen(prediction_buffer) > 0) {
        strncpy(result->prediction, prediction_buffer, sizeof(result->prediction) - 1);
    }
    
    if (score_found && strlen(score_buffer) > 0) {
        result->score = atof(score_buffer);
    }
    
    if (explanation_found && strlen(explanation_buffer) > 0) {
        strncpy(result->explanation, explanation_buffer, sizeof(result->explanation) - 1);
    }
    
    if (error_found && strlen(error_buffer) > 0) {
        strncpy(result->error, error_buffer, sizeof(result->error) - 1);
    }
    
    // Log the check
    log_url_check(url, result);
    
    return 0;
}

// Log URL security check result
void log_url_check(const char *url, const url_security_result_t *result) {
    if (!url || !result) return;
    
    // Create logs directory if it doesn't exist
    mkdir("logs", 0755);
    
    FILE *log_file = fopen("logs/url_security.log", "a");
    if (!log_file) return;
    
    time_t now = time(NULL);
    char timestamp[64];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", localtime(&now));
    
    fprintf(log_file, "[%s] URL: %s | Safe: %s | Prediction: %s | Score: %.3f | Explanation: %s\n",
            timestamp, url, 
            result->is_safe ? "YES" : "NO",
            result->prediction,
            result->score,
            result->explanation[0] ? result->explanation : "None");
    
    fclose(log_file);
}

// Generate HTML block page
char* get_block_page_html(const char *reason) {
    static char html[4096];
    
    snprintf(html, sizeof(html),
        "<!DOCTYPE html>"
        "<html>"
        "<head>"
            "<title>Access Blocked - Security Alert</title>"
            "<style>"
                "body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }"
                ".container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }"
                ".alert { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }"
                ".danger { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin: 20px 0; }"
                "h1 { color: #dc3545; }"
                ".details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }"
            "</style>"
        "</head>"
        "<body>"
            "<div class='container'>"
                "<h1>🚫 Access Blocked</h1>"
                "<div class='danger'>"
                    "<strong>Security Alert:</strong> This request has been blocked by the proxy server's malware detection system."
                "</div>"
                "<div class='details'>"
                    "<h3>Block Reason:</h3>"
                    "<p>%s</p>"
                "</div>"
                "<div class='alert'>"
                    "<strong>Note:</strong> This protection is provided by the integrated URL security middleware that analyzes URLs for potential threats including phishing, malware, and other malicious content."
                "</div>"
            "</div>"
        "</body>"
        "</html>", reason ? reason : "Unknown threat detected");
    
    return html;
}
