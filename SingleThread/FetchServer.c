#include "Headers.h"
#include <sys/time.h>
#include <stdio.h>      // printf()
#include <stdlib.h>     // malloc()
#include <string.h>     // memset()
#include <arpa/inet.h>  // ntop() etc
#include <sys/socket.h> // socket()
#include <netdb.h>      // getaddrinfo()
#include <unistd.h>     // close()

/*
        this function takes a hostname and path and sends a http response
        that the server will send us from the original request
*/


void FetchResServer(const char *host,const char *path, char **res,long double *ressize,long double *latency)

    /*
            a http GET request is of this format

            GET http://idk.com HTTP/1.1
            Host :idk.com:3040
            .................
            ..............
    */

    //      we know the host to which we call
{
    printf("Host: %s, Path: %s\n", host, path);

    struct addrinfo *iplist = getIP(host);
    if (!iplist) {
        fprintf(stderr, "DNS lookup failed for %s\n", host);
        *res = NULL; *ressize = 0; *latency = 0;
        return;
    }

    struct timeval tval_start, tval_end;
    gettimeofday(&tval_start, NULL);

    int serverSocketfd = -1;
    int total_bytes_recieved = 0;
    int curr_bytes_recieved = 0;

    // Try each address until one succeeds
    for (struct addrinfo *itr = iplist; itr; itr = itr->ai_next) {
        serverSocketfd = socket(itr->ai_family, itr->ai_socktype, itr->ai_protocol);
        if (serverSocketfd < 0) {
            perror("socket");
            continue;
        }
        if (connect(serverSocketfd, itr->ai_addr, itr->ai_addrlen) < 0) {
            perror("connect");
            close(serverSocketfd);
            continue;
        }

        // Build and send the GET
        char request[1024];
        snprintf(request, sizeof(request),
                 "GET /%s HTTP/1.1\r\n"
                 "Host: %s\r\n"
                 "Connection: close\r\n\r\n",
                 path, host);

        if (send(serverSocketfd, request, strlen(request), 0) < 0) {
            perror("send");
            close(serverSocketfd);
            // we already know iplist must be freed
            freeaddrinfo(iplist);
            *res = NULL; *ressize = 0; *latency = 0;
            return;
        }

        // Receive
        int bufSize = 1024;
        *res = malloc(bufSize);
        if (!*res) {
            perror("malloc");
            close(serverSocketfd);
            freeaddrinfo(iplist);
            *ressize = 0; *latency = 0;
            return;
        }

        total_bytes_recieved = 0;
        while ((curr_bytes_recieved = recv(serverSocketfd,
                                           *res + total_bytes_recieved,
                                           bufSize - total_bytes_recieved,
                                           0)) > 0)
        {
            total_bytes_recieved += curr_bytes_recieved;
            if (total_bytes_recieved == bufSize) {
                bufSize *= 2;
                char *tmp = realloc(*res, bufSize);
                if (!tmp) {
                    perror("realloc");
                    free(*res);
                    *res = NULL;
                    curr_bytes_recieved = -1;
                    break;
                }
                *res = tmp;
            }
        }

        // We got a response (or an error); stop trying other addresses
        break;
    }

    // Now that we’re done with DNS results, free them
    freeaddrinfo(iplist);

    // If recv errored out:
    if (curr_bytes_recieved < 0) {
        perror("recv");
        close(serverSocketfd);
        *res = NULL;
        *ressize = 0;
        *latency = 0;
        return;
    }

    // Measure latency and finish up
    gettimeofday(&tval_end, NULL);
    close(serverSocketfd);

    *ressize = total_bytes_recieved;
    *latency = (tval_end.tv_sec  - tval_start.tv_sec)
             + (tval_end.tv_usec - tval_start.tv_usec) / 1000000.0;
}