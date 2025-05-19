#include "Headers.h"

#include<stdio.h>       // printf()
#include<stdlib.h>      // malloc()
#include<string.h>      // memset()
#include <arpa/inet.h>  // ntop() etc
#include <sys/socket.h> // socket()
#include <netdb.h>       // getaddrinfo()
#include <unistd.h>       // close()



/*
        this function takes a http response and chcek if ot is present in the lru
        if present returns it from the lru 
        else calls the phase that will ask teh server for the response.
*/ 


void FetchResCache(char * req,int reqsize,char ** res,int * ressize ,LRUCache * cache){

        /*
                a http GET request is of this format 

                GET http://idk.com HTTP/1.1
                Host :idk.com:3040
                .................
                ..............
        */
        char httpMethord[16] , url[256] , protocol[16];
        // extract the important stuff from the first line

        if(sscanf(req,"%s %s %s",httpMethord,url,protocol)!=3){
                fprintf(stderr, "Invalid request format\n");
                return;
        }
        // check if it is a get request or not 
        if(strcmp(httpMethord,"GET")!=0){
                fprintf(stderr, "Only GET requests are supported\n");
                return;
        }

        /*
                the request path is like 
                http://idk.com/path
        */
        char host[256] , path[256] = "/";

        // check if the request has http:// in , it need to skip it 
        if (strncmp(url, "http://", 7) == 0)  
                sscanf(url + 7, "%[^/]/%s", host, path);
        else 
                sscanf(url, "%[^/]/%s", host, path);
        
        if (path[0] == '\0') {
            strcpy(path, "/"); // Default to root if no path
        }

        // now we know the host to which we call 
        printf("Host: %s, Path: %s\n", host, path);


        // check inside the lru
        CacheEntry * entry = lookupLRU(cache,host,path);

        if(entry != NULL){
                // result found
                printf("matching result found in the LRU\n");
                *res = entry->response;
                *ressize = entry->response_size;
                entry = NULL;
                return;
        }
        else{
                printf("result not found in the LRU aksing the server\n");
        }

        // if it was not present in the lru ask the next phase to call the server
        FetchResServer(host,path,res,ressize);

        // if result is still not found return
        if(*res == NULL){
                printf("Result was not fetched from the server\n");
                return;
        }
        else{
                // put it in lru
                insertLRU(cache,host,path,*res,*ressize);
                printf("Result fetched , stored in lru\n");
        }

}