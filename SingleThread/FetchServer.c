#include "Headers.h"

#include<stdio.h>       // printf()
#include<stdlib.h>      // malloc()
#include<string.h>      // memset()
#include <arpa/inet.h>  // ntop() etc
#include <sys/socket.h> // socket()
#include <netdb.h>       // getaddrinfo()
#include <unistd.h>       // close()


/*
        this function takes a http response and sends a http response
        that the server will send us from the original request
*/ 

void FetchRes(char * req,int reqsize,char ** res,int * ressize){

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

        struct addrinfo * iplist   = getIP(host);

        int serverSocketfd;

        for(struct addrinfo * itr = iplist ; itr!=NULL ; itr = itr->ai_next){  
                // since response is a linked list i can iterate over it

                // create a socket to connect to the server
                serverSocketfd = socket(itr->ai_family,itr->ai_socktype,itr->ai_protocol);
                if (serverSocketfd == -1) {
                        perror("socket");
                        continue; // Try the next address
                }       

                // connect to the server
                if(connect(serverSocketfd,itr->ai_addr,itr->ai_addrlen)==-1){
                        perror("connect");
                        close(serverSocketfd);
                        continue;
                }

                // lets make a minimal GET request of the one that ckient sent
                char request[1024];
                snprintf(request, sizeof(request),
                "GET /%s HTTP/1.1\r\n"
                "Host: %s\r\n"
                "Connection: close\r\n\r\n", path, host);

                // send http req to server
                if (send(serverSocketfd, request, strlen(request), 0) == -1) {
                        perror("send");
                        close(serverSocketfd);
                        return;
                }

                /*      RECIEVE THE RESPONSE DYNAMICALLY        */
                int responsebufferSize = 1024;
                *res = (char*)malloc(responsebufferSize);
                if(*res==NULL){
                        perror("malloc");
                        close(serverSocketfd);
                        return;
                }

                int total_bytes_recieved = 0;
                int curr_bytes_recieved = 0;
                while(( curr_bytes_recieved = recv(serverSocketfd,
                        *res +total_bytes_recieved,responsebufferSize-total_bytes_recieved,0) ) > 0){

                        total_bytes_recieved += curr_bytes_recieved;

                        if(total_bytes_recieved==responsebufferSize){
                                responsebufferSize *= 2;
                                *res = (char*)realloc(*res,responsebufferSize);

                                if(*res == NULL) {
                                        perror("realloc");
                                        curr_bytes_recieved = -1;
                                        break;
                                }
                        }

                }

                if (curr_bytes_recieved == -1) {
                        perror("recv");
                        free(res);
                        res = NULL;
                        return;
                }

                // store the response size
                *ressize =total_bytes_recieved;

                // close socket and break
                close(serverSocketfd);
                break;
        }

        freeaddrinfo(iplist);

}