
/*
LRU Cache structure
*/      

// This Structure Represents one cached entry in the LRU cache
typedef struct CacheEntry{
        char url[256];          // url string
        char path[256];         // path for url
        char *response;         // cached response address
        int response_size;
        struct CacheEntry * next;
        struct CacheEntry * prev;       // to make doubly linked list
}CacheEntry;


// This Represents the LRU Cache itself
typedef struct LRUCache{
        CacheEntry * head;      // start and end of lru
        CacheEntry * tail;
        int capacity;           // capacity
        int size;               // current size
        int hit_counter;        
        int miss_counter;       // further use
        
}LRUCache;



// LRU Cache Functions

//Function for Creating and initializing an LRU cache with the given capacity..
LRUCache *createLRU(int capacity);

// Function for Searching the cache for a given URL, and it returns pointer to the entry if found, else NULL
CacheEntry *lookupLRU(LRUCache *cache, const char *url,const char * path);

//Function for Inserting a new cache entry with URL and response data into the cache
void insertLRU(LRUCache *cache, const char *url,const char * path,char *response, int response_size);

//Function for Removing a cache entry identified by URL from the cache
void freeLRU(LRUCache *cache);





// other utilities
void FetchResServer(const char * host,const char * path,char ** res,int * ressize);

void FetchResCache(char * req,int reqsize,char ** res,int * ressize,LRUCache * cache);

struct addrinfo * getIP(const char * hostname );