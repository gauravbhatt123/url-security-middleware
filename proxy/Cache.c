#include "Headers.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// GDSF (Greedy Dual Size Frequency) Cache Implementation
// This cache ranks entries by frequency, latency, and size for eviction

static void removeEntry(optimisedcache *c, CacheEntry *e) {
    if (e->prev) {
        e->prev->next = e->next;
    } else {
        c->head = e->next;
    }
    if (e->next) {
        e->next->prev = e->prev;
    } else {
        c->tail = e->prev;
    }
}

static void insertByScore(optimisedcache *c, CacheEntry *e) {
    if (!c->head) {
        c->head = c->tail = e;
        e->prev = e->next = NULL;
        return;
    }
    
    // Insert at head if score is highest
    if (e->score >= c->head->score) {
        e->next = c->head;
        e->prev = NULL;
        c->head->prev = e;
        c->head = e;
        return;
    }
    
    // Insert at tail if score is lowest
    if (e->score <= c->tail->score) {
        e->prev = c->tail;
        e->next = NULL;
        c->tail->next = e;
        c->tail = e;
        return;
    }
    
    // Insert in middle based on score
    CacheEntry *cur = c->head->next;
    while (cur && cur->score >= e->score) {
        cur = cur->next;
    }
    e->next = cur;
    e->prev = cur->prev;
    cur->prev->next = e;
    cur->prev = e;
}

optimisedcache *createcache(long long capacity) {
    optimisedcache *c = calloc(1, sizeof *c);
    if (!c) {
        perror("createcache: malloc failed");
        return NULL;
    }
    c->capacity = capacity;
    c->size = 0;
    c->hit_counter = 0;
    c->miss_counter = 0;
    c->head = c->tail = NULL;
    return c;
}

CacheEntry *lookupcache(optimisedcache *c, const char *url, const char *path) {
    for (CacheEntry *e = c->head; e; e = e->next) {
        if (strcmp(e->url, url) == 0 && strcmp(e->path, path) == 0) {
            // Cache hit - update frequency and score
            ++c->hit_counter;
            ++e->frequency;
            e->score = (e->frequency * e->latency) / e->response_size;
            
            // Remove and reinsert to maintain score order
            removeEntry(c, e);
            insertByScore(c, e);
            return e;
        }
    }
    ++c->miss_counter;
    return NULL;
}

void insertcache(optimisedcache *c, const char *url, const char *path,
                 const char *response, long double response_size,
                 long double latency) {
    if (!c || !url || !path || !response || response_size <= 0) {
        return;
    }
    
    // Create a copy of the response
    char *dup = malloc((size_t)response_size + 1);
    if (!dup) {
        perror("insertcache: malloc failed");
        return;
    }
    memcpy(dup, response, (size_t)response_size);
    dup[(size_t)response_size] = '\0';

    // Create new cache entry
    CacheEntry *e = malloc(sizeof *e);
    if (!e) {
        perror("insertcache: malloc failed");
        free(dup);
        return;
    }
    
    strncpy(e->url, url, sizeof e->url - 1);
    e->url[sizeof e->url - 1] = '\0';
    strncpy(e->path, path, sizeof e->path - 1);
    e->path[sizeof e->path - 1] = '\0';
    e->response = dup;
    e->response_size = response_size;
    e->frequency = 1;
    e->latency = latency;
    e->score = (latency * 1.0L) / response_size;
    e->next = e->prev = NULL;

    // Insert into cache
    insertByScore(c, e);
    ++c->size;

    // Evict if cache is full (GDSF eviction)
    if (c->size > c->capacity) {
        CacheEntry *victim = c->tail;
        removeEntry(c, victim);
        free(victim->response);
        free(victim);
        --c->size;
    }
}

void freecache(optimisedcache *c) {
    if (!c) return;
    
    CacheEntry *e = c->head;
    while (e) {
        CacheEntry *next = e->next;
        free(e->response);
        free(e);
        e = next;
    }
    free(c);
}