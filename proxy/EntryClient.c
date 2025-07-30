/*
 * Multithreaded Proxy Server with Dynamic Buffering, Timeouts, and Robust Error Handling
 * Now with SO_REUSEADDR and SO_REUSEPORT to allow immediate re-bind after close.
 */

#include "Headers.h"    // Declarations for FetchRes(), getIP(), etc.
#include "MitmCert.h"

#include <stdio.h>      // printf(), perror()
#include <stdlib.h>     // malloc(), free(), exit()
#include <string.h>     // memset(), strstr(), strdup(), strlen()
#include <strings.h>    // strcasestr() - Added for GNU extension
#include <arpa/inet.h>  // sockaddr_storage, inet_ntop()
#include <sys/socket.h> // socket(), bind(), listen(), accept(), setsockopt(), recv(), send(), close()
#include <netdb.h>      // getaddrinfo(), freeaddrinfo()
#include <unistd.h>     // close()
#include <errno.h>      // errno, EWOULDBLOCK, EAGAIN
#include <sys/time.h>   // struct timeval
#include <pthread.h>    // pthreads
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <sys/select.h>
#include <sys/stat.h>
#include <sys/types.h>

// Initialize OpenSSL
// SSL_load_error_strings();
// OpenSSL_add_ssl_algorithms();

#define PORT "3040"     // Port to listen on
#define BACKLOG 10        // Max pending connections in queue
#define INIT_BUF 1024     // Initial buffer size for requests
#define TIMEOUT_SEC 5     // Socket recv/send timeout in seconds

// Global cache and its mutex
static optimisedcache *cache;
static pthread_mutex_t cache_mutex = PTHREAD_MUTEX_INITIALIZER;

// Thread argument struct  
typedef struct {
    int client_fd;
} thread_arg;

// Forward declaration of the per-client thread function
static void *handle_client(void *arg);

// Helper: Connect to target server (host:port)
int connect_to_server(const char *host, int port) {
    struct addrinfo hints = {0}, *res, *rp;
    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%d", port);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(host, port_str, &hints, &res) != 0) return -1;
    int fd = -1;
    for (rp = res; rp; rp = rp->ai_next) {
        fd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (fd < 0) continue;
        if (connect(fd, rp->ai_addr, rp->ai_addrlen) == 0) break;
        close(fd); fd = -1;
    }
    freeaddrinfo(res);
    return fd;
}

// Helper: Relay data between two sockets (bi-directional)
void relay_data(int fd1, int fd2) {
    fd_set fds;
    char buf[4096];
    int maxfd = fd1 > fd2 ? fd1 : fd2;
    while (1) {
        FD_ZERO(&fds);
        FD_SET(fd1, &fds);
        FD_SET(fd2, &fds);
        if (select(maxfd+1, &fds, NULL, NULL, NULL) <= 0) break;
        if (FD_ISSET(fd1, &fds)) {
            ssize_t n = recv(fd1, buf, sizeof(buf), 0);
            if (n <= 0) break;
            if (send(fd2, buf, n, 0) != n) break;
        }
        if (FD_ISSET(fd2, &fds)) {
            ssize_t n = recv(fd2, buf, sizeof(buf), 0);
            if (n <= 0) break;
            if (send(fd1, buf, n, 0) != n) break;
        }
    }
}

int main() {
    // Ensure proxy directory exists
    struct stat st = {0};
    if (stat("proxy", &st) == -1) {
        mkdir("proxy", 0700);
    }
    // Initialize OpenSSL
    SSL_load_error_strings();
    OpenSSL_add_ssl_algorithms();

    // Create SSL context for client
    SSL_CTX *client_ctx = SSL_CTX_new(TLS_server_method());
    if (!client_ctx) {
        fprintf(stderr, "SSL_CTX_new failed for client\n");
        exit(EXIT_FAILURE);
    }

    setvbuf(stdout, NULL, _IONBF, 0);
    struct addrinfo hints = {0}, *res;
    hints.ai_family   = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags    = AI_PASSIVE;
    if (getaddrinfo(NULL, PORT, &hints, &res) != 0) {
        perror("getaddrinfo");
        exit(EXIT_FAILURE);
    }

    int listen_fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (listen_fd < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    int yes = 1;
    // Allow reusing address
    if (setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes)) < 0) {
        perror("setsockopt(SO_REUSEADDR)");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }
    // Allow reusing port immediately after close
#ifdef SO_REUSEPORT
    if (setsockopt(listen_fd, SOL_SOCKET, SO_REUSEPORT, &yes, sizeof(yes)) < 0) {
        perror("setsockopt(SO_REUSEPORT)");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }
#endif

    if (bind(listen_fd, res->ai_addr, res->ai_addrlen) < 0) {
        perror("bind");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }
    freeaddrinfo(res);

    if (listen(listen_fd, BACKLOG) < 0) {
        perror("listen");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }
    printf("Proxy listening on port %s...\n", PORT);

    // Initialize cache
    cache = createcache(20);

    // Main accept loop
    while (1) {
        struct sockaddr_storage client_addr;
        socklen_t addr_len = sizeof client_addr;
        int client_fd = accept(listen_fd, (struct sockaddr *)&client_addr, &addr_len);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        pthread_t tid;
        thread_arg *arg = malloc(sizeof(*arg));
        arg->client_fd = client_fd;

        if (pthread_create(&tid, NULL, handle_client, arg) != 0) {
            perror("pthread_create");
            close(client_fd);
            free(arg);
            continue;
        }
        pthread_detach(tid);
    }

    // Cleanup OpenSSL
    SSL_CTX_free(client_ctx);
    EVP_cleanup();

    close(listen_fd);
    freecache(cache);
    pthread_mutex_destroy(&cache_mutex);
    return 0;
}

static void *handle_client(void *arg) {
    thread_arg *t = (thread_arg *)arg;
    int client_fd = t->client_fd;
    free(t);

    printf("[DEBUG] Accepted new connection: fd=%d\n", client_fd);

    struct timeval timeout = {TIMEOUT_SEC, 0};
    setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof timeout);
    setsockopt(client_fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof timeout);

    printf("[DEBUG] Starting recv loop for fd=%d\n", client_fd);

    size_t buf_size = INIT_BUF;
    char *buffer = malloc(buf_size);
    if (!buffer) { perror("malloc"); close(client_fd); return NULL; }
    size_t total_received = 0;
    ssize_t n;
    int got_any = 0;
    while ((n = recv(client_fd, buffer + total_received, buf_size - total_received - 1, 0)) > 0) {
        got_any = 1;
        total_received += n;
        buffer[total_received] = '\0';
        printf("[DEBUG] Received %zd bytes, total: %zu\n", n, total_received);
        if (strstr(buffer, "\r\n\r\n")) break;
        if (total_received + 1 >= buf_size) {
            buf_size *= 2;
            char *newbuf = realloc(buffer, buf_size);
            if (!newbuf) { perror("realloc"); free(buffer); close(client_fd); return NULL; }
            buffer = newbuf;
        }
    }
    if (!got_any) { perror("recv"); free(buffer); close(client_fd); return NULL; }
    if (total_received == 0) { free(buffer); close(client_fd); return NULL; }

    printf("[DEBUG] Received buffer: %s\n", buffer);
    char method[16], url[512], proto[16];
    if (sscanf(buffer, "%15s %511s %15s", method, url, proto) == 3) {
        printf("[DEBUG] Parsed method: %s, url: %s, proto: %s\n", method, url, proto);
        if (strcmp(method, "CONNECT") == 0) {
            printf("[DEBUG] Handling CONNECT (MITM)...\n");
            // --- MITM HTTPS logic (OpenSSL, SSL_accept, etc.) ---
            char host[256]; int port = 443;
            sscanf(url, "%255[^:]:%d", host, &port);

            if (generate_domain_cert(host) != 0) {
                const char *err = "HTTP/1.1 502 Bad Gateway\r\n\r\n";
                send(client_fd, err, strlen(err), 0);
                free(buffer); close(client_fd); return NULL;
            }
            const char *ok = "HTTP/1.1 200 Connection Established\r\n\r\n";
            send(client_fd, ok, strlen(ok), 0);

            SSL_CTX *mitm_ctx = SSL_CTX_new(TLS_server_method());
            char certfile[300], keyfile[300];
            snprintf(certfile, sizeof(certfile), "proxy/%s.crt", host);
            snprintf(keyfile, sizeof(keyfile), "proxy/%s.key", host);
            printf("[DEBUG] certfile: %s\n", certfile);
            printf("[DEBUG] keyfile: %s\n", keyfile);
            FILE *fc = fopen(certfile, "r");
            if (!fc) { perror("[DEBUG] fopen certfile"); }
            else { fclose(fc); }
            FILE *fk = fopen(keyfile, "r");
            if (!fk) { perror("[DEBUG] fopen keyfile"); }
            else { fclose(fk); }
            printf("[DEBUG] Loading certificate...\n");
            if (SSL_CTX_use_certificate_file(mitm_ctx, certfile, SSL_FILETYPE_PEM) != 1) {
                perror("[DEBUG] SSL_CTX_use_certificate_file");
                ERR_print_errors_fp(stderr);
                SSL_CTX_free(mitm_ctx);
                free(buffer); close(client_fd); return NULL;
            }
            printf("[DEBUG] Loading private key...\n");
            if (SSL_CTX_use_PrivateKey_file(mitm_ctx, keyfile, SSL_FILETYPE_PEM) != 1) {
                perror("[DEBUG] SSL_CTX_use_PrivateKey_file");
                ERR_print_errors_fp(stderr);
                SSL_CTX_free(mitm_ctx);
                free(buffer); close(client_fd); return NULL;
            }
            printf("[DEBUG] Starting SSL_accept...\n");
            SSL *ssl_client = SSL_new(mitm_ctx);
            SSL_set_fd(ssl_client, client_fd);
            int ssl_accept_result = SSL_accept(ssl_client);
            printf("[DEBUG] SSL_accept result: %d\n", ssl_accept_result);
            if (ssl_accept_result <= 0) {
                perror("[DEBUG] SSL_accept");
                ERR_print_errors_fp(stderr);
                SSL_free(ssl_client); SSL_CTX_free(mitm_ctx);
                free(buffer); close(client_fd); return NULL;
            }

            int server_fd = connect_to_server(host, port);
            if (server_fd < 0) {
                SSL_free(ssl_client); SSL_CTX_free(mitm_ctx);
                free(buffer); close(client_fd); return NULL;
            }
            SSL_CTX *server_ctx = SSL_CTX_new(TLS_client_method());
            SSL *ssl_server = SSL_new(server_ctx);
            SSL_set_fd(ssl_server, server_fd);
            if (SSL_connect(ssl_server) <= 0) {
                ERR_print_errors_fp(stderr);
                SSL_free(ssl_server); SSL_CTX_free(server_ctx);
                SSL_free(ssl_client); SSL_CTX_free(mitm_ctx);
                close(server_fd); free(buffer); close(client_fd);
                return NULL;
            }

            fd_set fds;
            char buf[4096];
            int maxfd = client_fd > server_fd ? client_fd : server_fd;
            
            // First, read the HTTPS request from client to parse it
            char https_req[8192] = {0};
            int https_req_len = 0;
            int req_complete = 0;
            
            // Read HTTPS request (similar to HTTP but over SSL)
            while (!req_complete && https_req_len < sizeof(https_req) - 1) {
                int n_ssl = SSL_read(ssl_client, https_req + https_req_len, sizeof(https_req) - https_req_len - 1);
                if (n_ssl <= 0) break;
                https_req_len += n_ssl;
                https_req[https_req_len] = '\0';
                printf("[DEBUG] Read %d bytes from client, total: %d\n", n_ssl, https_req_len);
                
                // Check if we have complete headers
                if (strstr(https_req, "\r\n\r\n")) {
                    req_complete = 1;
                    break;
                }
            }
            
            if (https_req_len > 0 && req_complete) {
                printf("[DEBUG] HTTPS Request length: %d\n", https_req_len);
                printf("[DEBUG] HTTPS Request: %s\n", https_req);
                
                // Parse HTTPS request (same format as HTTP)
                char https_method[16], https_url[512], https_proto[16];
                if (sscanf(https_req, "%15s %511s %15s", https_method, https_url, https_proto) == 3) {
                    printf("[DEBUG] HTTPS Parsed method: %s, url: %s, proto: %s\n", https_method, https_url, https_proto);
                    
                    if (strcmp(https_method, "GET") == 0) {
                        // Extract path from URL (HTTPS requests typically have just the path)
                        char path[256] = "/";
                                                 strncpy(path, https_url, sizeof(path) - 1);
                         path[sizeof(path) - 1] = '\0';
                         if (path[0] == '\0') strncpy(path, "/", sizeof(path) - 1);
                        
                        // Extract host from Host header
                        char req_host[256] = "";
                        char *host_line = strstr(https_req, "Host:");
                        if (host_line) {
                            host_line += 5; // Skip "Host:"
                            while (*host_line == ' ' || *host_line == '\t') host_line++;
                            char *end = strchr(host_line, '\r');
                            if (end) *end = '\0';
                            strncpy(req_host, host_line, sizeof(req_host) - 1);
                            req_host[sizeof(req_host) - 1] = '\0';
                        }
                        
                        printf("[DEBUG] HTTPS Host=%s Path=%s\n", req_host, path);
                        
                                                 // Check cache first for HTTPS requests
                         pthread_mutex_lock(&cache_mutex);
                         CacheEntry *https_cache_entry = lookupcache(cache, req_host, path);
                         pthread_mutex_unlock(&cache_mutex);
                         
                         if (https_cache_entry) {
                             printf("[DEBUG] HTTPS Cache HIT, serving from cache\n");
                             // Send cached response to client via SSL
                             if (SSL_write(ssl_client, https_cache_entry->response, https_cache_entry->response_size) > 0) {
                                 printf("[DEBUG] Sent cached HTTPS response to client\n");
                             }
                             pthread_mutex_lock(&cache_mutex);
                             print_cache_state(cache);
                             pthread_mutex_unlock(&cache_mutex);
                             printf("\n");
                             SSL_shutdown(ssl_client);
                             SSL_free(ssl_client); SSL_CTX_free(mitm_ctx);
                             free(buffer); close(client_fd);
                             return NULL;
                         }
                         
                         printf("[DEBUG] HTTPS Cache MISS, fetching from server\n");
                        
                        // Use the existing HTTP flow to fetch the response
                        char *response = NULL;
                        long double response_size = 0;
                        long double latency = 0.0L;
                        
                        // Measure start time for latency
                        struct timeval start_time, end_time;
                        gettimeofday(&start_time, NULL);
                        
                        // Use FetchResServer to get the response via HTTP
                        FetchResServer(req_host, path, &response, &response_size, &latency);
                        
                        gettimeofday(&end_time, NULL);
                        latency = (end_time.tv_sec - start_time.tv_sec) + (end_time.tv_usec - start_time.tv_usec) / 1000000.0L;
                        
                        // Cache and send the response
                        if (response && response_size > 0) {
                            printf("[DEBUG] HTTPS Response size: %Lf, latency: %Lf\n", response_size, latency);
                            printf("[DEBUG] First 200 chars of response: %.200s\n", response);

                                                         // Insert HTTPS response into cache
                             pthread_mutex_lock(&cache_mutex);
                             insertcache(cache, req_host, path, response, response_size, latency);
                             pthread_mutex_unlock(&cache_mutex);
                             printf("[DEBUG] HTTPS response cached successfully\n");
                             print_cache_state(cache);
                             printf("\n");

                            // Send the response to the client via SSL
                            if (SSL_write(ssl_client, response, response_size) > 0) {
                                printf("[DEBUG] Sent HTTPS response to client\n");
                            }
                            SSL_shutdown(ssl_client);
                            free(response);
                                                 } else {
                             // Send error response if no response was received
                             const char *error_response = "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n";
                             SSL_write(ssl_client, error_response, strlen(error_response));
                             pthread_mutex_lock(&cache_mutex);
                             print_cache_state(cache);
                             pthread_mutex_unlock(&cache_mutex);
                             printf("\n");
                             SSL_shutdown(ssl_client);
                         }
                        
                        SSL_free(ssl_client); SSL_CTX_free(mitm_ctx);
                        free(buffer); close(client_fd);
                        return NULL;
                    }
                }
                        
                // If not a GET request or parsing failed, fall back to simple relay
                while (1) {
                    FD_ZERO(&fds);
                    FD_SET(client_fd, &fds);
                    FD_SET(server_fd, &fds);
                    if (select(maxfd+1, &fds, NULL, NULL, NULL) <= 0) break;
                    if (FD_ISSET(client_fd, &fds)) {
                        int n_ssl_read = SSL_read(ssl_client, buf, sizeof(buf));
                        if (n_ssl_read <= 0) break;
                        if (SSL_write(ssl_server, buf, n_ssl_read) != n_ssl_read) break;
                    }
                    if (FD_ISSET(server_fd, &fds)) {
                        int n_ssl_read = SSL_read(ssl_server, buf, sizeof(buf));
                        if (n_ssl_read <= 0) break;
                        if (SSL_write(ssl_client, buf, n_ssl_read) != n_ssl_read) break;
                    }
                }
                SSL_free(ssl_server); SSL_CTX_free(server_ctx);
                SSL_free(ssl_client); SSL_CTX_free(mitm_ctx);
                close(server_fd); free(buffer); close(client_fd);
                return NULL;
            }
        } else {
            printf("[DEBUG] Handling plain HTTP...\n");
            char *response = NULL;
            long double res_len = -1, latency = 0.0L;
            pthread_mutex_lock(&cache_mutex);
            FetchResCache(buffer, total_received, &response, &res_len, cache, &latency);
            print_cache_state(cache);
            printf("\n");
            pthread_mutex_unlock(&cache_mutex);
            free(buffer);
            if (!response || res_len < 0) {
                const char *err500 =
                    "HTTP/1.1 500 Internal Server Error\r\n"
                    "Content-Type: text/html\r\n"
                    "Content-Length: 53\r\n"
                    "\r\n"
                    "<html><body><h1>500 Internal Server Error</h1></body></html>";
                response = strdup(err500);
                res_len = strlen(err500);
            } else {
                // For HTTP, we can serve the response directly since it's already formatted
                // The response from FetchResCache should already have proper HTTP headers
            }
            fprintf(stderr, ">>> PROXY → CLIENT (%Lf ms):\n%.*s\n", latency*1000,
                    (int)res_len, response);
            ssize_t sent = 0;
            while (sent < (ssize_t)res_len) {
                ssize_t n_send = send(client_fd, response + sent, res_len - sent, 0);
                if (n_send < 0) {
                    perror("send");
                    break;
                }
                sent += n_send;
            }
                         printf("Sent %zd bytes back to client. Latency => %.6Lf\n", sent, latency);
             pthread_mutex_lock(&cache_mutex);
             print_cache_state(cache);
             pthread_mutex_unlock(&cache_mutex);
             printf("\n");
             free(response);
             close(client_fd);
             return NULL;
        }
    }
    // If we get here, sscanf parsing failed or another error occurred before dispatch.
    free(buffer);
    close(client_fd);
    return NULL;
}