/*
 * Multithreaded Proxy Server with Dynamic Buffering, Timeouts, and Robust Error Handling
 * Listens on PORT, accepts connections, dispatches each to its own thread.
 */

#include "Headers.h"    // Declarations for FetchRes(), getIP(), etc.

#include <stdio.h>      // printf(), perror()
#include <stdlib.h>     // malloc(), free(), exit()
#include <string.h>     // memset(), strstr(), strdup(), strlen()
#include <arpa/inet.h>  // sockaddr_storage, inet_ntop()
#include <sys/socket.h> // socket(), bind(), listen(), accept(), setsockopt(), recv(), send(), close()
#include <netdb.h>      // getaddrinfo(), freeaddrinfo()
#include <unistd.h>     // close()
#include <errno.h>      // errno, EWOULDBLOCK, EAGAIN
#include <sys/time.h>   // struct timeval
#include <pthread.h>    // pthreads

#define PORT "3490"     // Port to listen on
#define BACKLOG 10      // Max pending connections in queue
#define INIT_BUF 1024   // Initial buffer size for requests
#define TIMEOUT_SEC 5   // Socket recv/send timeout in seconds

// Global cache and its mutex
static optimisedcache *cache;
static pthread_mutex_t cache_mutex = PTHREAD_MUTEX_INITIALIZER;

// Thread argument struct
typedef struct {
    int client_fd;
} thread_arg;

// Forward declaration of the per-client thread function
static void *handle_client(void *arg);

int main()
{
    // Prepare hints for getaddrinfo
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
    if (setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes) < 0) {
        perror("setsockopt");
        close(listen_fd);
        exit(EXIT_FAILURE);
    }

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
    cache = createcache(5);

    // Main accept loop
    while (1) {
        struct sockaddr_storage client_addr;
        socklen_t addr_len = sizeof client_addr;
        int client_fd = accept(listen_fd, (struct sockaddr *)&client_addr, &addr_len);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        // Spawn a detached thread to handle this client
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

    // Never reached
    close(listen_fd);
    freecache(cache);
    pthread_mutex_destroy(&cache_mutex);
    return 0;
}

static void *handle_client(void *arg) {
    thread_arg *t = (thread_arg *)arg;
    int client_fd = t->client_fd;
    free(t);

    // Set timeouts on client socket
    struct timeval timeout = {TIMEOUT_SEC, 0};
    setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof timeout);
    setsockopt(client_fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof timeout);

    // Read request headers
    size_t buf_size = INIT_BUF;
    char *buffer = malloc(buf_size);
    if (!buffer) {
        perror("malloc");
        close(client_fd);
        return NULL;
    }
    size_t total_received = 0;
    ssize_t n;
    while ((n = recv(client_fd, buffer + total_received,
                     buf_size - total_received - 1, 0)) > 0) {
        total_received += n;
        buffer[total_received] = '\0';
        if (strstr(buffer, "\r\n\r\n")) break;
        if (total_received + 1 >= buf_size) {
            buf_size *= 2;
            char *newbuf = realloc(buffer, buf_size);
            if (!newbuf) {
                perror("realloc");
                free(buffer);
                close(client_fd);
                return NULL;
            }
            buffer = newbuf;
        }
    }
    if (!buffer || (n < 0 && errno != EWOULDBLOCK && errno != EAGAIN)) {
        perror("recv");
        free(buffer);
        close(client_fd);
        return NULL;
    }
    if (total_received == 0) {
        free(buffer);
        close(client_fd);
        return NULL;
    }
    printf("Received request (\"%.*s...\")\n", 50, buffer);

    // Forward via cache (protected by cache_mutex)
    char *response = NULL;
    long double res_len = -1, latency = 0.0L;

    pthread_mutex_lock(&cache_mutex);
    FetchResCache(buffer, total_received, &response, &res_len, cache, &latency);
    print_cache_state(cache);
    printf("\n");
    pthread_mutex_unlock(&cache_mutex);

    free(buffer);

    // On error, send 500
    if (!response || res_len < 0) {
        const char *err500 =
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: 53\r\n"
            "\r\n"
            "<html><body><h1>500 Internal Server Error</h1></body></html>";
        response = strdup(err500);
        res_len = strlen(err500);
    }

    // Send response
    ssize_t sent = 0;
    while (sent < res_len) {
        n = send(client_fd, response + sent, res_len - sent, 0);
        if (n < 0) {
            perror("send");
            break;
        }
        sent += n;
    }
    printf("Sent %zd bytes back to client. Latency => %.6Lf\n", sent, latency);

    free(response);
    close(client_fd);
    return NULL;
}
