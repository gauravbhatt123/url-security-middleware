# 🔁 Multithreaded Proxy Server with Optimized Caching

A high-performance, C-powered HTTP proxy that serves concurrent clients with a smart caching layer—evicting not just by recency but by a dynamic score blending access frequency and latency.

🚀 Project Overview

This project implements a high-performance, multithreaded HTTP proxy server in C. It listens for client connections, forwards requests to target servers, and accelerates repeat access with a custom intelligent cache that outperforms basic LRU by factoring in how often and how slow content is.

Key highlights:

Concurrent: One thread per client using POSIX threads.

Dynamic Caching: Evicts entries based on a score = (frequency × latency) / size.

Resilient: Timeouts, robust error handling, and graceful evictions.

🎯 Goals & Milestones

Completed ✅

Socket-Based Proxy: Listens on a TCP port, accepts raw HTTP connections.

Multithreading: Spawns a thread for each incoming client (POSIX threads).

Request Parsing: Correctly handles and forwards HTTP GET requests.

Smart Cache: Frequency + latency + size → priority-based eviction.

Thread Safety: All cache operations guarded by pthread_mutex_t.

In Progress 🚧

Streaming / Chunked Responses

Detailed Access Logging & Perf Metrics

CLI Configuration (cache size, thread pool, log level)

🧠 Optimized Cache Design

Unlike traditional LRU (least-recently used), our cache ranks entries by a dynamic score:

Frequency Count: How many times an object is requested.

Latency Measurement: Round-trip time to fetch if not cached.

Size Normalization: Larger objects have proportionally lower priority.

Score formula:

score = (frequency × latency_ms) / response_size_bytes

Entries with higher scores stay longer in the cache, ensuring that slow-loading or popular resources stick around.

🧱 System Architecture

[Client] → [Proxy Thread Pool]
                 ↓
          [Cache Module]
            ↙       ↘
      Hit → Serve   Miss → Fetch → Cache → Serve

Client Handler Threads: Each client is handled in its own POSIX thread.

Cache Module: A doubly-linked list sorted by score.

Synchronization: pthread_mutex_t locks around all shared data.

🔧 Tech Stack

Component

Purpose

C (GCC)

Core implementation

pthread.h

Multithreading

sys/socket.h

TCP socket programming

arpa/inet.h

IP address utilities

netdb.h

DNS lookup

unistd.h, fcntl.h

Low-level I/O & timeouts

🧪 Quickstart & Testing

Compile:

gcc EntryClient.c FetchServer.c LRU.c CallDns.c ClientToServer.c CacheData.c -o proxy -pthread

Run:

./proxy 3490          # listens on port 3490

Test with curl:

curl -x http://localhost:3490 http://example.com

Browser:

HTTP Proxy: localhost:3490 (no HTTPS yet)

📌 Assumptions & Limitations

POSIX-compliant system (Linux, macOS).

HTTP GET only; no POST, HTTPS, or streaming support yet.

Educational/demo quality, not hardened for untrusted environments.

🚀 Next Steps

Add streaming/chunked response handling.

Expose CLI flags for cache size, thread count, and log verbosity.

Integrate detailed metrics & visualizations.

Made with ❤️ by the Proxy Squad

