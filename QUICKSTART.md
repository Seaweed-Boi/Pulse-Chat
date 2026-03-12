# Pulse-Chat Quick Start Guide

## 1. Generate SSL Certificates (First Time Only)

```bash
cd certs
./generate_certs.sh
cd ..
```

## 2. Start the Server

```bash
python run_server.py
```

You should see:
```
======================================================================
PULSE-CHAT SECURE SERVER
======================================================================

[SERVER] Secure chat server started on 0.0.0.0:5555
[SERVER] Using certificate: certs/server.crt
[SERVER] Waiting for connections...
```

## 3. Start Multiple Clients (in separate terminals)

**Terminal 1:**
```bash
python run_client.py localhost 5555 Alice
```

**Terminal 2:**
```bash
python run_client.py localhost 5555 Bob
```

**Terminal 3:**
```bash
python run_client.py localhost 5555 Charlie
```

Each client will prompt for a username (if not provided) and connect securely.

## 4. Chat!

- Type any message and press Enter
- Messages are broadcast to all connected clients
- Type `/quit` to disconnect

## Common Issues

### "Certificate files not found"
Run the certificate generation script:
```bash
cd certs && ./generate_certs.sh
```

### "Address already in use"
The server is already running, or port is in use. Try:
```bash
# Kill existing process
lsof -ti:5555 | xargs kill -9

# Or use a different port
python run_server.py 0.0.0.0 8080
```

### "Connection refused"
Make sure the server is running first before starting clients.

## Testing the System

1. Start server
2. Open 3 terminal windows and start 3 clients
3. Send messages from different clients
4. Close one client (Ctrl+C or `/quit`)
5. Verify other clients see the leave message
6. Observe server logs for connection details

## Project Structure Overview

```
Pulse-Chat/
├── server/
│   ├── chat_server.py          # Main server (TCP, SSL, threading)
│   └── client_handler.py       # Per-client thread handler
├── client/
│   └── chat_client.py          # Client implementation
├── utils/
│   └── message_protocol.py     # JSON message format
├── certs/
│   ├── generate_certs.sh       # Certificate generator
│   ├── server.key              # Private key (generated)
│   └── server.crt              # Public certificate (generated)
├── run_server.py               # Start server
└── run_client.py               # Start client
```

## Key Files to Review

1. **utils/message_protocol.py** - Understand message format
2. **server/chat_server.py** - Server setup, SSL, threading
3. **server/client_handler.py** - Client communication
4. **client/chat_client.py** - Client implementation

## For Your Course Report

This implementation demonstrates:
- ✅ TCP socket programming (server and client)
- ✅ SSL/TLS encryption with self-signed certificates
- ✅ Multi-threaded server for concurrent clients
- ✅ Message broadcasting architecture
- ✅ Graceful disconnect handling
- ✅ JSON-based message protocol
- ✅ Thread-safe shared resource access

All code includes detailed comments explaining networking concepts!
