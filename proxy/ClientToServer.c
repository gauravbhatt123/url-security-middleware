#include "Headers.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/*
    This function takes the raw HTTP request in `req` (size `reqsize`),
    checks the GDSF cache, and if it’s a miss calls FetchResServer.
    On a hit, returns a strdup’ed copy and sets *latency = 0.
    On a miss, measures latency, inserts into cache, and returns the server result.
*/
void FetchResCache(char *req,
                   long double          reqsize,
                   char      **res,
                   long double         *ressize,
                   optimisedcache *cache,
                   long double *latency)
{
    char method[16], url[512], proto[16];
    if (sscanf(req, "%15s %511s %15s", method, url, proto) != 3) {
        fprintf(stderr, "Invalid request format\n");
        *res = NULL;
        *ressize = 0;
        *latency = 0;
        return;
    }
    if (strcmp(method, "GET") != 0) {
        fprintf(stderr, "Only GET supported\n");
        *res = NULL;
        *ressize = 0;
        *latency = 0;
        return;
    }

    // Extract host and path
    char host[256], path[256] = "/";
    if (strncmp(url, "https://", 8) == 0) {
        sscanf(url + 8, "%255[^/]/%255[^\n]", host, path + 1);
    } else if (strncmp(url, "http://", 7) == 0) {
        sscanf(url + 7, "%255[^/]/%255[^\n]", host, path + 1);
    } else {
        sscanf(url, "%255[^/]/%255[^\n]", host, path + 1);
    }
    if (path[0] == '\0') strcpy(path, "/");

    printf("FetchResCache: Host=%s Path=%s\n", host, path);

    // 1) Try GDSF cache
    CacheEntry *e = lookupcache(cache, host, path);
    if (e) {
        printf("Cache HIT\n");
        // return a copy so caller can free
        *res      = strdup(e->response);
        *ressize  = e->response_size;
        *latency  = 0.0L;
        return;
    }
    printf("Cache MISS, fetching from server\n");

    // 2) Miss → fetch from origin, measure latency
    FetchResServer(host, path, res, ressize, latency);
    if (!*res || *ressize <= 0) {
        fprintf(stderr, "FetchResServer failed\n");
        *res      = NULL;
        *latency  = 0.0L;
        return;
    }

    // 3) Insert into GDSF cache (transfers ownership of *res)
    insertcache(cache, host, path, *res, *ressize, *latency);
    printf("Inserted into cache: size=%lld/%lld\n",
           cache->size, cache->capacity);
}
