#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <time.h>


#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <semaphore.h>

// using namespace std;

// Global declaration
int default_port = 3000;
void find();
void erase();
void add();

// LRU cache
struct cache_element{
    // priority_queue<tuple<int , string>, vector<tuple<int, string>>, greater<tuple<int , string>>>pq;
    int len;
    char* url;
    char *datareceive;
    time_t lru_time_track;
    struct cache_element* next; //linklist for LRU cache    
}cache_element;

/*
what will be the number of max client that can req to the tcp socket at a time, should we put it 1 or 1e5
if 1 then we will be making 1 thread at a time 
but for larger n is it even possible to make 1e5 thread -> inner sockets for connections
lets see
*/
// Define a semaphore
// Define a mutex lock

//Global declaration for first part

//semaphore max capacity i initialized with 10
// so the number of max thread will be form at a single time is 10;
const int MAX_THREAD = 10;

int proxy_socketid;
pthread_t tid[MAX_THREAD];
sem_t semaphore;


void receiveReq(){
    int client_socketid, client_length;
    struct sockaddr_in server_address, client_address;

    sem_init(&semaphore, 0, MAX_THREAD); //(semaphore, intial_Value, Max_capacity)
    pthread_mutex_init(&lock, NULL);


    // making socket for proxy web server (Main_ Socket)
    // here AF_INET use ipv4 addressing for storing client ip in 32-bit addrs
    // SOCK_STREAM create a stream socket
    proxy_socketid = socket(AF_INET, SOCK_STREAM, 0 /*default protocol*/);
    if(proxy_socketid  == -1){
        printf("Socket is not formed\n");
        exit(1);
    }
    printf("Socket id - %d", proxy_socketid);

    //reuse the socket if it is free;
    int reuse = 1;
    if(setsockopt(proxy_socketid, SOL_SOCKET, SO_REUSEADDR, (const char*)&reuse, sizeof(reuse)) == -1){
        printf("SetSock Option failed\n");
        exit(1);
    }

    clear(server_address);
    clear(client_address);
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(default_port);
    server_address.sin_addr.s_addr = INADDR_ANY;
    if(bind(proxy_socketid, (struct sockaddr*)&server_address, sizeof(server_address)) == -1){
        printf("Port is not available %d\n", default_port);
        exit(1);
    }
    printf("Binding on port %d\n", default_port);

    // socket will start listning from here

    int listen_status = listen(proxy_socketid, MAX_THREAD);
    if(listen_status == -1){
        printf("Socket not responding\n");
        exit(1);
    }
    //Here i store all the ip of client which are connected to the socket right now for the future response
    int connected_socketId_array[MAX_THREAD];
    int i =0;
    while(i < MAX_THREAD){
        memset(&client_address, 0, sizeof(client_address));
        client_length = sizeof(client_address);
        client_socketid = accept(proxy_socketid, (const struct sockaddr *)&client_address, (socklen_t*)&client_length); //acceptiing request and Returns a new socket file descriptor 
        if(client_socketid == -1){
            printf("Socket not responding\n");
            exit(1);
        }
        connected_socketId_array[i++] = client_socketid;
    }

    struct sockaddr_in *client_pt = (struct sockaddr_in *)&client_address;
    struct in_addr ip_addr = client_pt-> sin_addr; //client ip address (raw format)
    char str[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &ip_addr, str, INET6_ADDRSTRLEN); //convert ip address to presentable format
    /* This  function converts the network address structure src in the af address family into a character string.  The resulting string is copied to the buffer pointed to by dst, which must be a non-null pointer.  The caller specifies
   the number of bytes available in this buffer in the argument size.

    inet_ntop() extends the inet_ntoa(3) function to support multiple address families, inet_ntoa(3) is now considered to be deprecated in favor of inet_ntop().
    */

    printf("Client is connected with the tcp port %d and ip address of client is %s\n", ntohs(client_address.sin_port), str);



}


//Global Declaration 
pthread_mutex_t lock;
void LRU_Cache(){}



void sendResponse(){}




int main(){
    int choice;
    printf("Enter localhost port number (Default - 3000)\n");
    scanf("%d", &choice);
    default_port = choice;
    printf("Starting new port at www.localhost: %d\n", choice);
    receiveReq();
    LRU_cache();
    sendResponse();

}

