#!/usr/bin/env python3
"""
Server Entry Point

Run this script to start the Pulse-Chat server.

Usage:
    python run_server.py [host] [port]

Examples:
    python run_server.py                    # Default: 0.0.0.0:5555
    python run_server.py localhost 8080     # Custom host and port
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.chat_server import ChatServer


def main():
    """Start the chat server with optional command-line arguments."""
    
    # Parse command-line arguments
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
    
    # Certificate paths
    cert_file = 'certs/server.crt'
    key_file = 'certs/server.key'
    
    # Check if certificates exist
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("=" * 70)
        print("ERROR: SSL certificates not found!")
        print("=" * 70)
        print(f"\nRequired files:")
        print(f"  - {cert_file}")
        print(f"  - {key_file}")
        print(f"\nPlease generate certificates first:")
        print(f"  cd certs")
        print(f"  sh generate_certs.sh")
        print()
        return
    
    # Create and start the server
    print("=" * 70)
    print("PULSE-CHAT SECURE SERVER")
    print("=" * 70)
    print()
    
    server = ChatServer(
        host=host,
        port=port,
        cert_file=cert_file,
        key_file=key_file
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()


if __name__ == "__main__":
    main()
