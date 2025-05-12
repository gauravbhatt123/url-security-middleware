

/*
        This function takes the hostname as input and returns a linked list
        of ip address that corresponds to that hostname 

        This is done by using a similar process where you local dns is asked 
        to contact root dns and so on 
        
*/

#include "Headers.h"

#include <stdio.h>      // printf() 
#include <stdlib.h>     // malloc() , exit(1)
#include <string.h>     // memset()
#include <netdb.h>      // getaddinfo() 
#include <arpa/inet.h>  // for ip related tasks , convert the ip to different format

struct addrinfo * getIP(char * hostname){
        
        struct addrinfo req , *res;    
        // req will tell the library what we need and the response is lined list of type addrinfo

        int status;     // getinfoaddr() also returns a status

        memset(&req,0,sizeof(req));     // remove garbage from memory


        /*
                this just means any ip address is welcomes ipv4 or v6
                and we wil use a relient connection like TCP
        */
        req.ai_family = AF_UNSPEC;
        req.ai_socktype = SOCK_STREAM;


        status = getaddrinfo(hostname,"80",&req,&res);
        // NULL param : you can request port as well , on success we get 0 else non zero

        if(status!=0){
                fprintf(stderr,"getaddrinfo gave an error: %s\n",gai_strerror(status));
                // gai_strerro converts the error given by getaddrinfo to a readable string
                return NULL;
        }

        return res;
}


