#include "Headers.h"

#include<stdio.h>       // printf()
#include<stdlib.h>      // malloc()
#include<string.h>      // memset()
#include <arpa/inet.h>  // ntop() etc
#include <sys/socket.h> // socket()
#include <netdb.h>       // getaddrinfo()
#include <unistd.h>       // close()


/*
        this function takes a hostname and path and sends a http response
        that the server will send us from the original request
*/ 

void FetchResServer(const char * host,const char * path,char ** res,int * ressize){

        /*
                a http GET request is of this format 

                GET http://idk.com HTTP/1.1
                Host :idk.com:3040
                .................
                ..............
        */

        //      we know the host to which we call 
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
                // this is done to dynamically keep track of the size of the respose

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