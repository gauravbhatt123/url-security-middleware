#define _POSIX_C_SOURCE 200112L
#include "Headers.h"
#include <stdio.h>

void print_cache_state(optimisedcache *c) {
    if (!c) {
        printf("Cache is NULL\n");
        return;
    }
    
    printf("=== Cache State ===\n");
    printf("Size  : %lld / %lld\n", c->size, c->capacity);
    printf("Hits  : %lld\n", c->hit_counter);
    printf("Misses: %lld\n", c->miss_counter);

    int idx = 1;
    for (CacheEntry *e = c->head; e; e = e->next, ++idx) {
        printf("Entry %d: %s%s  size=%.0Lf  freq=%lld  score=%.3Lf\n",
               idx, e->url, e->path, e->response_size, e->frequency, e->score);
    }
    if (!c->head) {
        printf("Cache empty\n");
    }
    printf("===================\n");
}