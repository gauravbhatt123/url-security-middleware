#include "Headers.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// NOTE : the most recently used element is in the head

// Create a new LRU cache with a fixed capacity
LRUCache *createLRU(int capacity){
        LRUCache *cache = (LRUCache *)malloc(sizeof(LRUCache));
        cache->head = NULL;
        cache->tail = NULL;  // Initially empty
        cache->capacity = capacity;  // Fixed capacity as requested
        cache->size = 0;  // No entries yet
        cache->hit_counter = 0;  // No hits yet
        cache->miss_counter = 0;
        return cache;
}


// Function to find an entry in the cache by url and path
CacheEntry *lookupLRU(LRUCache *cache, const char *url,const char * path) {
        CacheEntry *itr = cache->head;

        while(itr != NULL){
                // Checks if this entry matches the URL
                if(strcmp(itr->url, url) == 0 && strcmp(itr->path,path) == 0){
                        // Found Moving this entry to the front (most recently used)
                        if(itr != cache->head){
                                // remove it
                                if (itr->prev != NULL ) itr->prev->next = itr->next;
                                if (itr->next != NULL) itr->next->prev = itr->prev;
                                // if found at tail update tail
                                if(itr == cache->tail) cache->tail = itr->prev;    
                                // update head
                                itr->prev = NULL;
                                itr->next = cache->head;
                                if(cache->head!=NULL) cache->head->prev = itr;
                                cache->head = itr;
                        }
                        // Increasing the hit counter
                        cache->hit_counter++;
                        return itr;  // Returning the found entry
                }
                itr = itr->next;
        }
        cache-> miss_counter++;
        return NULL;  // Returning NULL if entry Not found
}



// Function to Insert a new entry into the cache
void insertLRU(LRUCache *cache, const char *url,const char * path ,char *response, int response_size) {

        // Creating a new cache entry
        CacheEntry *entry = (CacheEntry *)malloc(sizeof(CacheEntry));
        strncpy(entry->url, url, sizeof(entry->url) - 1);
        entry->url[sizeof(entry->url) - 1] = '\0';
        strncpy(entry->path, path, sizeof(entry->path) - 1);
        entry->path[sizeof(entry->path) - 1] = '\0';

        entry->response = response;     // store the dynamic address
        entry->response_size = response_size;
        entry->prev = NULL;  


        // Inserting the entry at the front (most recently used)
        entry->next = cache->head;  
        if(cache->head != NULL) cache->head->prev = entry;
        else cache->tail = entry;
        cache->head = entry;
        cache->size++;  


        // If we have exceeded the capacity,Then removing the least recently used (tail)
        if(cache->size > cache->capacity){
                CacheEntry *remove = cache->tail;
                if(remove->prev!=NULL){
                        cache->tail = remove->prev;
                        cache->tail->next = NULL;
                }
                else{
                        cache->head = NULL;
                        cache->tail = NULL;  // Empty cache
                }
                free(remove->response);  // Free the response memory
                remove->response = NULL;
                remove->next = NULL;
                remove->prev = NULL;
                free(remove);  // Free the entry itself
                cache->size--;
        }
}


//Function to free the memory
void freeLRU(LRUCache * cache){
        CacheEntry * itr = cache->head , *nextitr = NULL;
        while(itr!=NULL){
                nextitr = itr->next;
                free(itr->response);
                itr->response = NULL;
                itr->next = NULL;
                itr->prev = NULL;
                free(itr);
                itr = nextitr;
        }
        cache->head = NULL;
        cache->tail = NULL;
        itr = NULL;
        nextitr = NULL;
        free(cache);
}