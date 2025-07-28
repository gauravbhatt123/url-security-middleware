#include "Headers.h"
#include <sys/time.h>
#include <stdio.h>      // printf(), fprintf(), perror()
#include <stdlib.h>     // malloc(), realloc(), free()
#include <string.h>     // memset(), strlen()
#include <errno.h>      // errno, EAGAIN, EWOULDBLOCK
#include <arpa/inet.h>  // ntop() etc
#include <sys/socket.h> // socket(), setsockopt(), SOL_SOCKET, SO_RCVTIMEO, SO_SNDTIMEO
#include <netdb.h>      // getaddrinfo(), freeaddrinfo()
#include <unistd.h>     // close()
#include <openssl/ssl.h>
#include <openssl/err.h>

#define SOCK_TIMEOUT_SECS 5      // seconds for send/recv timeout
#define MAX_RETRIES       3      // number of full GET retries

void FetchResServer(const char *host,
                    const char *path,
                    char **res,
                    long double *ressize,
                    long double *latency)
{
    *res = NULL;
    *ressize = 0;
    *latency = 0;

    struct addrinfo *iplist = getIP(host);
    if (!iplist) {
        fprintf(stderr, "DNS lookup failed for %s\n", host);
        return;
    }

    struct timeval tval_start, tval_end;
    int attempt;
    for (attempt = 1; attempt <= MAX_RETRIES; ++attempt) {
        gettimeofday(&tval_start, NULL);

        int serverSocketfd = -1;
        int bufSize = 1024;
        int total_bytes_received = 0;
        int curr_bytes_received = 0;
        char *buffer = NULL;

        // Try each resolved address
        for (struct addrinfo *itr = iplist; itr; itr = itr->ai_next) {
            // 1) create socket
            serverSocketfd = socket(itr->ai_family,
                                    itr->ai_socktype,
                                    itr->ai_protocol);
            if (serverSocketfd < 0) {
                perror("socket");
                continue;
            }

            // 2) set send/recv timeouts
            struct timeval sock_timeout = { SOCK_TIMEOUT_SECS, 0 };
            setsockopt(serverSocketfd, SOL_SOCKET, SO_RCVTIMEO,
                       &sock_timeout, sizeof(sock_timeout));
            setsockopt(serverSocketfd, SOL_SOCKET, SO_SNDTIMEO,
                       &sock_timeout, sizeof(sock_timeout));

            // 3) connect to the server
            if (connect(serverSocketfd,
                        itr->ai_addr,
                        itr->ai_addrlen) < 0) {
                perror("connect");
                close(serverSocketfd);
                continue;
            }

            // 4) build & send HTTP GET
            char request[1024];
            snprintf(request, sizeof(request),
                     "GET %s HTTP/1.1\r\n"
                     "Host: %s\r\n"
                     "User-Agent: curl/8.15.0\r\n"
                     "Accept: */*\r\n"
                     "Connection: close\r\n\r\n",
                     path, host);

            if (send(serverSocketfd,
                     request,
                     strlen(request), 0) < 0) {
                perror("send");
                close(serverSocketfd);
                break;
            }

            // 5) receive loop
            buffer = malloc(bufSize);
            if (!buffer) {
                perror("malloc");
                close(serverSocketfd);
                break;
            }

            total_bytes_received = 0;
            while ((curr_bytes_received = recv(
                        serverSocketfd,
                        buffer + total_bytes_received,
                        bufSize - total_bytes_received,
                        0)) > 0) {
                total_bytes_received += curr_bytes_received;
                if (total_bytes_received == bufSize) {
                    bufSize *= 2;
                    char *tmp = realloc(buffer, bufSize);
                    if (!tmp) {
                        perror("realloc");
                        free(buffer);
                        buffer = NULL;
                        curr_bytes_received = -1;
                        break;
                    }
                    buffer = tmp;
                }
            }

            // close socket whether we succeeded or hit timeout/error
            close(serverSocketfd);

             if (curr_bytes_received < 0) {

                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    // Case 1: Timed out
                    fprintf(stderr,
                        "Attempt %d: recv() timed out after %d seconds\n",
                        attempt, SOCK_TIMEOUT_SECS);
                } 
                else if (total_bytes_received == 0) {
                    // Case 2: Error and nothing was read at all
                    fprintf(stderr,
                        "Attempted recv() failed, no data received from the server\n");
                } 
                else {
                    // Case 3: Error after some data was received
                    fprintf(stderr,
                        "Attempt recv() failed, partial read failure\n");
                }

                free(buffer);
                buffer = NULL;
                continue;  // try next address or retry
            }

            // break out of address loop on any non-timeout result
            break;
        }

        if (buffer && total_bytes_received > 0) {
            // success
            gettimeofday(&tval_end, NULL);
            *latency = (tval_end.tv_sec  - tval_start.tv_sec)
                     + (tval_end.tv_usec - tval_start.tv_usec) / 1e6;
            *ressize = total_bytes_received;
            *res = buffer;
            break;
        }

        // if we get here, either buffer==NULL or recv error: retry
        fprintf(stderr, "Attempt %d failed, retrying...\n", attempt);
    }

    if (attempt > MAX_RETRIES) {
        fprintf(stderr,
                "All %d attempts failed; giving up.\n",
                MAX_RETRIES);
    }

    freeaddrinfo(iplist);
}
