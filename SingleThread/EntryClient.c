/*
 * Single-Threaded Proxy Server with Dynamic Buffering, Timeouts, and Robust Error Handling
 * Listens on PORT, accepts connections, processes each sequentially.
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

#define PORT "3490"   // Port to listen on
#define BACKLOG 10    // Max pending connections in queue
#define INIT_BUF 1024 // Initial buffer size for requests
#define TIMEOUT_SEC 5 // Socket recv/send timeout in seconds

int main()
{
        // Prepare hints for getaddrinfo: IPv4/IPv6, TCP, passive for binding
        struct addrinfo hints = {0}, *res;
        hints.ai_family = AF_UNSPEC;     // Allow IPv4 or IPv6
        hints.ai_socktype = SOCK_STREAM; // TCP stream sockets
        hints.ai_flags = AI_PASSIVE;     // Use wildcard IP (INADDR_ANY)
        // Resolve local address and port
        if (getaddrinfo(NULL, PORT, &hints, &res) != 0)
        {
                perror("getaddrinfo");
                exit(EXIT_FAILURE);
        }

        // Create listening socket
        int listen_fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
        if (listen_fd < 0)
        {
                perror("socket");
                exit(EXIT_FAILURE);
        }

        // Allow immediate reuse of the port after program exit
        int yes = 1;
        if (setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes) < 0)
        {
                perror("setsockopt");
                close(listen_fd);
                exit(EXIT_FAILURE);
        }

        // Bind socket to resolved address and port
        if (bind(listen_fd, res->ai_addr, res->ai_addrlen) < 0)
        {
                perror("bind");
                close(listen_fd);
                exit(EXIT_FAILURE);
        }
        freeaddrinfo(res); // Done with address info

        // Start listening for incoming connections
        if (listen(listen_fd, BACKLOG) < 0)
        {
                perror("listen");
                close(listen_fd);
                exit(EXIT_FAILURE);
        }
        printf("Proxy listening on port %s...\n", PORT);

        // initialize our lru to be used
        int capacity = 5;
        optimisedcache *cache = createcache(capacity);

        // Main loop: accept and handle one client at a time
        while (1)
        {
                printf("Cache print hora h\n");
                print_cache_state(cache);
                printf("\n");
                struct sockaddr_storage client_addr;
                socklen_t addr_len = sizeof(client_addr);

                // Wait for a client to connect
                int client_fd = accept(listen_fd,
                                       (struct sockaddr *)&client_addr,
                                       &addr_len);
                if (client_fd < 0)
                {
                        perror("accept");
                        continue; // Try next connection
                }

                // Set timeouts to avoid blocking forever
                struct timeval timeout = {TIMEOUT_SEC, 0};
                setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof timeout);
                setsockopt(client_fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof timeout);

                // Dynamically read the full HTTP request headers
                size_t buf_size = INIT_BUF;
                char *buffer = malloc(buf_size);
                if (!buffer)
                {
                        perror("malloc");
                        close(client_fd);
                        continue;
                }
                size_t total_received = 0;
                ssize_t n;
                while ((n = recv(client_fd, buffer + total_received,
                                 buf_size - total_received - 1, 0)) > 0)
                {
                        total_received += n;
                        buffer[total_received] = '\0';
                        if (strstr(buffer, "\r\n\r\n"))
                                break; // End of headers
                        if (total_received + 1 >= buf_size)
                        {
                                buf_size *= 2;
                                char *newbuf = realloc(buffer, buf_size);
                                if (!newbuf)
                                {
                                        perror("realloc");
                                        free(buffer);
                                        close(client_fd);
                                        buffer = NULL;
                                        break;
                                }
                                buffer = newbuf;
                        }
                }
                if (!buffer || (n < 0 && errno != EWOULDBLOCK && errno != EAGAIN))
                {
                        perror("recv");
                        free(buffer);
                        close(client_fd);
                        continue;
                }
                if (total_received == 0)
                {
                        free(buffer);
                        close(client_fd);
                        continue;
                }
                printf("Received request (\"%.*s...\")\n", 50, buffer);

                // Forward request and obtain response
                char *response = NULL;
                long double res_len = -1;
                long double latency = 0.0L;
                FetchResCache(buffer,total_received,&response,&res_len,cache, &latency);
                free(buffer);

                // On error, prepare a default 500 response
                if (!response || res_len < 0)
                {
                        const char *err500 =
                            "HTTP/1.1 500 Internal Server Error\r\n"
                            "Content-Type: text/html\r\n"
                            "Content-Length: 53\r\n"
                            "\r\n"
                            "<html><body><h1>500 Internal Server Error</h1></body></html>";
                        response = strdup(err500);
                        res_len = strlen(err500);
                }

                // Send entire response, handling partial writes
                ssize_t sent = 0;
                while (sent < res_len)
                {
                        n = send(client_fd, response + sent, res_len - sent, 0);
                        if (n < 0)
                        {
                                perror("send");
                                break;
                        }
                        sent += n;
                }
                printf("Sent %zd bytes back to client.\n", sent);
                printf("Latency => %.6Lf\n", latency);

                // Clean up
                close(client_fd);
        }

        // Cleanup listening socket (never reached)
        close(listen_fd);
        freecache(cache);
        return 0;
}
