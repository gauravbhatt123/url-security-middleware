#include "Headers.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stddef.h>

static void removeEntry(optimisedcache *cache, CacheEntry *e) {
    if (e->prev) e->prev->next = e->next;
    else         cache->head = e->next;

    if (e->next) e->next->prev = e->prev;
    else         cache->tail = e->prev;
}

static void insertByScore(optimisedcache *cache, CacheEntry *e) {
    // empty?
    if (!cache->head) {
        cache->head = cache->tail = e;
        e->prev = e->next = NULL;
        return;
    }

    // highest‐score at head
    if (e->score >= cache->head->score) {
        e->next = cache->head;
        e->prev = NULL;
        cache->head->prev = e;
        cache->head = e;
        return;
    }
    // lowest‐score at tail
    if (e->score <= cache->tail->score) {
        e->prev = cache->tail;
        e->next = NULL;
        cache->tail->next = e;
        cache->tail = e;
        return;
    }
    // middle: find first node with score < e->score and insert before it
    CacheEntry *cur = cache->head->next;
    while (cur && cur->score >= e->score) {
        cur = cur->next;
    }
    // cur now has cur->score < e->score
    e->next        = cur;
    e->prev        = cur->prev;
    cur->prev->next = e;
    cur->prev      = e;
}


optimisedcache *createcache(long long capacity) {
    optimisedcache *c = malloc(sizeof *c);
    c->head = c->tail = NULL;
    c->capacity = capacity;
    c->size = c->hit_counter = c->miss_counter = 0;
    return c;
}

CacheEntry *lookupcache(optimisedcache *cache, const char *url, const char *path) {
    for (CacheEntry *e = cache->head; e; e = e->next) {
        if (strcmp(e->url, url)==0 && strcmp(e->path, path)==0) {
            cache->hit_counter++;
            // update frequency & score
            e->frequency++;
            e->score = (e->frequency * e->latency) / (long double)e->response_size;
            // reposition
            removeEntry(cache, e);
            insertByScore(cache, e);
            return e;
        }
    }
    cache->miss_counter++;
    return NULL;
}

void insertcache(optimisedcache *cache,
                 const char *url, const char *path,
                 char *response, long double response_size,
                 long double latency) {
    CacheEntry *e = malloc(sizeof *e);
    strncpy(e->url, url, sizeof e->url);
    strncpy(e->path, path, sizeof e->path);
    e->response      = response;
    e->response_size = response_size;
    e->frequency     = 1;
    e->latency       = latency;
    e->score         = (latency * e->frequency) / (long double)response_size;
    // splice in
    insertByScore(cache, e);
    cache->size++;

    // evict lowest‐priority if over capacity
    if (cache->size > cache->capacity) {
        CacheEntry *victim = cache->tail;
        removeEntry(cache, victim);
        free(victim->response);
        free(victim);
        cache->size--;
    }
}

void freecache(optimisedcache *cache) {
    CacheEntry *e = cache->head;
    while (e) {
        CacheEntry *next = e->next;
        free(e->response);
        free(e);
        e = next;
    }
    free(cache);
}
