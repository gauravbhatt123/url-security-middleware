#include "Headers.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void FetchResCache(char *req, long double reqsize,
                   char **res, long double *ressize,
                   optimisedcache *cache, long double *latency) {
    (void)reqsize; /* suppress unused warning */

    char method[16], url[512], proto[16];
    if (sscanf(req, "%15s %511s %15s", method, url, proto) != 3) {
        *res = NULL; 
        *ressize = 0; 
        *latency = 0; 
        return;
    }
    
    if (strcmp(method, "GET") != 0) {
        *res = NULL; 
        *ressize = 0; 
        *latency = 0; 
        return;
    }

    // Parse URL to extract host and path
    char host[256] = "", path[256] = "/";
    if (strncmp(url, "http://", 7) == 0) {
        sscanf(url + 7, "%255[^/]%255s", host, path);
    } else if (strncmp(url, "https://", 8) == 0) {
        sscanf(url + 8, "%255[^/]%255s", host, path);
    } else {
        sscanf(url, "%255[^/]%255s", host, path);
    }

    // Check cache first
    CacheEntry *e = lookupcache(cache, host, path);
    if (e) {
        // Cache hit - return cached response
        *res = malloc((size_t)e->response_size + 1);
        if (!*res) {
            perror("FetchResCache: malloc failed for cache hit");
            *ressize = 0;
            *latency = 0;
            return;
        }
        memcpy(*res, e->response, (size_t)e->response_size);
        (*res)[(size_t)e->response_size] = '\0';
        *ressize = e->response_size;
        *latency = 0.0L; // Cache hit has zero latency
        return;
    }

    // Cache miss - fetch from server and cache the result
    FetchResServer(host, path, res, ressize, latency);
    if (*res && *ressize > 0) {
        insertcache(cache, host, path, *res, *ressize, *latency);
    }
}