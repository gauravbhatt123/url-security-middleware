#include "Headers.h" 
#include <stdio.h>
void print_cache_state(optimisedcache *cache) {
    printf("Cache State Starting\n");
    printf("Cache Size: %lld / %lld\n", cache->size, cache->capacity);
    printf("Cache Hits: %lld, Cache Misses: %lld\n\n", cache->hit_counter, cache->miss_counter);

    CacheEntry *curr = cache->head;
    int index = 1;
    while (curr != NULL) {
        printf("Entry %d:\n", index++);
        printf("  URL     : %s\n", curr->url);
        printf("  Path    : %s\n", curr->path);
        printf("  Size    : %.2Lf bytes\n", curr->response_size);
        printf("  Freq    : %lld\n", curr->frequency);
        printf("  Latency : %.6Lf ms\n", curr->latency);
        printf("  Score   : %.6Lf\n", curr->score);
        printf("Cache State Ending\n");

        curr = curr->next;
    }

    if (index == 1) {
        printf("Cache is empty.\n");
    }
}