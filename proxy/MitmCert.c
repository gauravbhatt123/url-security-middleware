#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>

int generate_domain_cert(const char *domain) {
    char cmd[1024];
    char keyfile[256], csrfile[256], certfile[256], configfile[256];
    
    // Create file paths in proxy/ subdirectory
    snprintf(keyfile, sizeof(keyfile), "proxy/%s.key", domain);
    snprintf(csrfile, sizeof(csrfile), "proxy/%s.csr", domain);
    snprintf(certfile, sizeof(certfile), "proxy/%s.crt", domain);
    snprintf(configfile, sizeof(configfile), "proxy/%s.cnf", domain);
    
    // Generate private key
    snprintf(cmd, sizeof(cmd), "openssl genrsa -out %s 2048", keyfile);
    if (system(cmd) != 0) {
        fprintf(stderr, "Failed to generate private key for %s\n", domain);
        return -1;
    }
    
    // Create OpenSSL config file with SAN
    FILE *config = fopen(configfile, "w");
    if (!config) {
        fprintf(stderr, "Failed to create config file for %s\n", domain);
        return -1;
    }
    fprintf(config, "[req]\n");
    fprintf(config, "distinguished_name = req_distinguished_name\n");
    fprintf(config, "req_extensions = v3_req\n");
    fprintf(config, "prompt = no\n");
    fprintf(config, "[req_distinguished_name]\n");
    fprintf(config, "C = US\n");
    fprintf(config, "ST = State\n");
    fprintf(config, "L = City\n");
    fprintf(config, "O = Organization\n");
    fprintf(config, "OU = Organizational Unit\n");
    fprintf(config, "CN = %s\n", domain);
    fprintf(config, "[v3_req]\n");
    fprintf(config, "keyUsage = keyEncipherment, dataEncipherment\n");
    fprintf(config, "extendedKeyUsage = serverAuth\n");
    fprintf(config, "subjectAltName = @alt_names\n");
    fprintf(config, "[alt_names]\n");
    fprintf(config, "DNS.1 = %s\n", domain);
    fprintf(config, "DNS.2 = *.%s\n", domain);
    fclose(config);
    
    // Generate CSR
    snprintf(cmd, sizeof(cmd), 
             "openssl req -new -key %s -out %s -config %s",
             keyfile, csrfile, configfile);
    if (system(cmd) != 0) {
        fprintf(stderr, "Failed to generate CSR for %s\n", domain);
        unlink(configfile);
        return -1;
    }
    
    // Sign with our CA
    snprintf(cmd, sizeof(cmd),
             "openssl x509 -req -in %s -CA mitmproxyCA.crt -CAkey mitmproxyCA.key "
             "-CAcreateserial -out %s -days 365 -extensions v3_req -extfile %s",
             csrfile, certfile, configfile);
    if (system(cmd) != 0) {
        fprintf(stderr, "Failed to sign certificate for %s\n", domain);
        unlink(configfile);
        return -1;
    }
    
    // Set permissions
    chmod(keyfile, 0600);
    chmod(certfile, 0644);
    
    // Clean up temporary files
    unlink(csrfile);
    unlink(configfile);
    
    printf("Certificate request self-signature ok\n");
    printf("subject=CN=%s\n", domain);
    
    return 0;
} 