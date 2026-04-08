#!/usr/bin/env python3
"""Simple entry point for starting the Pulse-Chat server."""

import sys
import os
import socket

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.chat_server import ChatServer


def print_usage():
    """Show basic command usage."""
    print("Usage:")
    print("  python run_server.py [host] [port]")
    print()
    print("Examples:")
    print("  python run_server.py")
    print("  python run_server.py localhost 8080")


def get_lan_ip():
    """Best-effort LAN IP detection for connecting from another device."""
    probe_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe_socket.connect(("8.8.8.8", 80))
        return probe_socket.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe_socket.close()


def parse_arguments():
    """Read host and port from the command line."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        return None

    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    try:
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
    except ValueError:
        print("Error: port must be a number.")
        print_usage()
        return None

    return host, port


def main():
    """Start the chat server."""
    parsed = parse_arguments()
    if parsed is None:
        return

    host, port = parsed
    cert_file = "certs/server.crt"
    key_file = "certs/server.key"

    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        print("=" * 70)
        print("ERROR: SSL certificates not found!")
        print("=" * 70)
        print()
        print("Required files:")
        print(f"  - {cert_file}")
        print(f"  - {key_file}")
        print()
        print("Please generate certificates first:")
        print("  cd certs")
        print("  sh generate_certs.sh")
        print()
        return

    print("=" * 70)
    print("PULSE-CHAT SECURE SERVER")
    print("=" * 70)
    print()
    lan_ip = get_lan_ip()
    print(f"Server LAN address: {lan_ip}")
    print(f"Clients on another laptop can connect to: {lan_ip}:{port}")
    print()

    server = ChatServer(
        host=host,
        port=port,
        cert_file=cert_file,
        key_file=key_file,
    )

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()


if __name__ == "__main__":
    main()
