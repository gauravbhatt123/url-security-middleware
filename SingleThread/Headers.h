
/*
LRU Cache structure
*/      

// This Structure Represents one cached entry in the LRU cache
typedef struct CacheEntry{
        char url[256];          // url string
        char path[256];         // path for url
        char *response;         // cached response address
        long double response_size;

        long long int frequency;
        long double latency;
        long double score;


        struct CacheEntry * next;
        struct CacheEntry * prev;       // to make doubly linked list
}CacheEntry;


// This Represents the LRU Cache itself
typedef struct optimisedcache{
        CacheEntry * head;      // start and end of lru
        CacheEntry * tail;
        long long int capacity;           // capacity
        long long int size;               // current size
        long long int hit_counter;        
        long long int miss_counter;       // further use
        
}optimisedcache;



// LRU Cache Functions

//Function for Creating and initializing an LRU cache with the given capacity..
optimisedcache *createcache(long long int capacity);

// Function for Searching the cache for a given URL, and it returns pointer to the entry if found, else NULL
CacheEntry *lookupcache(optimisedcache *cache, const char *url,const char * path);

//Function for Inserting a new cache entry with URL and response data into the cache
void insertcache(optimisedcache *cache, const char *url,const char * path,char *response, long double response_size, long double latency_ms);

//Function for Removing a cache entry identified by URL from the cache
void freecache(optimisedcache *cache);





// other utilities
void FetchResServer(const char * host,const char * path,char ** res,long double * ressize, long double *latency);

void FetchResCache(char * req,long double reqsize,char ** res,long double * ressize,optimisedcache * cache, long double *latency);

struct addrinfo * getIP(const char * hostname );
void print_cache_state(optimisedcache *cache);