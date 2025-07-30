#ifndef HEADERS_H
#define HEADERS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
#include <sys/time.h>
#include <pthread.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

/* ---------- CACHE ---------- */
typedef struct CacheEntry {
    char        url[256];
    char        path[256];
    char       *response;
    long double response_size;
    long long   frequency;
    long double latency;
    long double score;
    struct CacheEntry *next;
    struct CacheEntry *prev;
} CacheEntry;

typedef struct {
    CacheEntry *head;
    CacheEntry *tail;
    long long   capacity;
    long long   size;
    long long   hit_counter;
    long long   miss_counter;
} optimisedcache;

optimisedcache *createcache(long long capacity);
CacheEntry     *lookupcache(optimisedcache *, const char *url, const char *path);
void            insertcache(optimisedcache *, const char *url, const char *path,
                            const char *response, long double response_size,
                            long double latency);
void            freecache(optimisedcache *);

/* ---------- PROXY CORE ---------- */
void  FetchResServer(const char *host, const char *path,
                     char **res, long double *ressize, long double *latency);
void  FetchResCache(char *req, long double reqsize,
                    char **res, long double *ressize,
                    optimisedcache *cache, long double *latency);
struct addrinfo *getIP(const char *hostname);
void print_cache_state(optimisedcache *cache);

/* ---------- MITM ---------- */
int generate_domain_cert(const char *domain);

#endif