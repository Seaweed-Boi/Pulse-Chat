#!/usr/bin/env python3
"""
Client Entry Point

Run this script to start a Pulse-Chat client and connect to the server.

Usage:
    python run_client.py [host] [port] [username]

Examples:
    python run_client.py                        # Default: localhost:5555
    python run_client.py localhost 8080         # Custom host and port
    python run_client.py localhost 5555 Alice   # With username
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.chat_client import ChatClient


def main():
    """Start a chat client with optional command-line arguments."""
    
    # Parse command-line arguments
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
    username = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Display banner
    print("=" * 70)
    print("PULSE-CHAT CLIENT")
    print("=" * 70)
    print()
    
    # Create and start the client
    client = ChatClient(
        server_host=host,
        server_port=port,
        username=username
    )
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()


if __name__ == "__main__":
    main()
