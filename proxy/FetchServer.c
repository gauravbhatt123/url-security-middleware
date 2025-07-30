#define _POSIX_C_SOURCE 200112L
#include "Headers.h"
#include <sys/time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>

// getIP function is defined in CallDns.c

void FetchResServer(const char *host, const char *path,
                    char **res, long double *ressize,
                    long double *latency) {
    *res = NULL; 
    *ressize = 0; 
    *latency = 0;

    struct addrinfo *ai = getIP(host);
    if (!ai) {
        fprintf(stderr, "DNS lookup failed for %s\n", host);
        return;
    }

    struct timeval start, end;
    for (int try = 0; try < 3; ++try) {
        gettimeofday(&start, NULL);
        int sock = -1;
        
        // Try to connect to each address
        for (struct addrinfo *p = ai; p; p = p->ai_next) {
            sock = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
            if (sock < 0) continue;
            
            // Set socket timeouts
            struct timeval tv = {5, 0};
            setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
            setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof tv);
            
            if (connect(sock, p->ai_addr, p->ai_addrlen) == 0) {
                break;
            }
            close(sock); 
            sock = -1;
        }
        
        if (sock < 0) {
            fprintf(stderr, "Failed to connect to %s (attempt %d)\n", host, try + 1);
            continue;
        }

        // Construct HTTP request
        char req[1024];
        int len = snprintf(req, sizeof req,
                           "GET %s HTTP/1.1\r\n"
                           "Host: %s\r\n"
                           "User-Agent: proxy/1.0\r\n"
                           "Accept: */*\r\n"
                           "Connection: close\r\n\r\n",
                           path, host);
        
        if (send(sock, req, len, 0) < 0) {
            fprintf(stderr, "Failed to send request to %s\n", host);
            close(sock);
            continue;
        }

        // Receive response
        size_t cap = 4096, total = 0;
        char *buf = malloc(cap);
        if (!buf) {
            perror("FetchResServer: malloc failed");
            close(sock);
            continue;
        }
        
        ssize_t n;
        while ((n = recv(sock, buf + total, cap - total, 0)) > 0) {
            total += n;
            if (total == cap) {
                cap *= 2;
                char *newbuf = realloc(buf, cap);
                if (!newbuf) {
                    perror("FetchResServer: realloc failed");
                    free(buf);
                    close(sock);
                    goto next_try;
                }
                buf = newbuf;
            }
        }
        close(sock);
        
        if (total > 0) {
            gettimeofday(&end, NULL);
            *latency = (end.tv_sec - start.tv_sec) +
                       (end.tv_usec - start.tv_usec) / 1e6;
            *res = realloc(buf, total + 1);
            if (!*res) {
                perror("FetchResServer: final realloc failed");
                free(buf);
                break;
            }
            (*res)[total] = '\0';
            *ressize = total;
            break;
        }
        free(buf);
        
next_try:
        continue;
    }
    freeaddrinfo(ai);
}