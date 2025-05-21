# 🔁 Multithreaded Proxy Server with Optimized Caching

A high-performance, C-powered HTTP proxy that serves concurrent clients with a smart caching layer—evicting not just by recency but by a dynamic score blending access frequency and latency.

🚀 Project Overview

This project implements a high-performance, single-threaded HTTP proxy server in C. It listens for one client connection at a time, forwards requests to target servers, and accelerates repeat access with a custom intelligent cache that outperforms basic LRU by factoring in how often and how slow content is.

Key highlights:

Sequential Handling: Processes each client connection one by one in a loop.

Dynamic Caching: Evicts entries based on a score = (frequency × latency) / size.

Resilient: Implements timeouts, robust error handling, and graceful evictions.

🎯 Goals & Milestones

Completed ✅

Socket-Based Proxy: Listens on a TCP port, accepts raw HTTP connections.

Sequential Client Loop: Handles one client at a time in the main loop.

Request Parsing: Correctly handles and forwards HTTP GET requests.

Smart Cache: Frequency + latency + size → priority-based eviction.

Cache State Printing: Dump cache contents and metrics on demand.

In Progress 🚧

Streaming / Chunked Responses

Detailed Access Logging & Perf Metrics

CLI Configuration (cache size, timeout, log level)

Multithreading: Upgrade to a thread-per-connection model

🧠 Optimized Cache Design

Unlike traditional LRU (least-recently used), our cache ranks entries by a dynamic score:

Frequency Count: Number of times a resource is requested.

Latency Measurement: Round-trip time to fetch if not cached.

Size Normalization: Larger objects have proportionally lower priority.

Score formula:

score = (frequency × latency_ms) / response_size_bytes

Entries with higher scores remain in the cache longer, ensuring that slow-loading or popular resources stick around.

🧱 System Architecture

[Main Loop]
    └─ accept() → handle one client → close()
           ↓
     [Cache Module]
       ↙       ↘
 Hit → serve   Miss → fetch → cache → serve

Sequential Handler: Accepts and processes clients one after another.

Cache Module: A doubly-linked list sorted by score.

Timeouts & Errors: Uses SO_RCVTIMEO/SO_SNDTIMEO and default 500 responses on failure.

🔧 Tech Stack

Component

Purpose

C (GCC)

Core implementation

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

gcc EntryClient.c FetchServer.c LRU.c CallDns.c ClientToServer.c CacheData.c -o proxy

Run:

./proxy 3490          # listens on port 3490

Test with curl:

curl -x http://localhost:3490 http://example.com

Browser:

HTTP Proxy: localhost:3490 (no HTTPS or concurrency yet)

📌 Assumptions & Limitations

POSIX-compliant system (Linux, macOS).

Single-threaded: processes one connection at a time.

HTTP GET only; no POST, HTTPS, or streaming support yet.

Educational/demo quality, not hardened for production.

🚀 Next Steps

Add streaming/chunked response handling.

Expose CLI flags for cache size, timeout, and log verbosity.

Implement multithreading with POSIX threads.

Integrate detailed metrics & visualizations.

Made with ❤️ by the Proxy Squad
