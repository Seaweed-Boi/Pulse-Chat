#!/usr/bin/env python3
"""Simple entry point for starting the Pulse-Chat client."""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.chat_client import ChatClientApp, TerminalChatClient


def print_usage():
    """Show basic command usage."""
    print("Usage:")
    print("  python run_client.py [host] [port] [username] [--cli]")
    print()
    print("Examples:")
    print("  python run_client.py")
    print("  python run_client.py localhost 8080")
    print("  python run_client.py localhost 5555 Alice")
    print("  python run_client.py --cli")


def parse_arguments():
    """Read command-line values and return client settings."""
    cli_mode = "--cli" in sys.argv
    help_requested = "--help" in sys.argv or "-h" in sys.argv

    if help_requested:
        print_usage()
        return None

    args = []
    for value in sys.argv[1:]:
        if value not in ("--cli", "--help", "-h"):
            args.append(value)

    host = args[0] if len(args) > 0 else "localhost"
    username = args[2] if len(args) > 2 else None

    try:
        port = int(args[1]) if len(args) > 1 else 5555
    except ValueError:
        print("Error: port must be a number.")
        print_usage()
        return None

    return host, port, username, cli_mode


def gui_is_available():
    """Check whether tkinter can be imported and opened."""
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
        return True, ""
    except Exception as error:
        return False, str(error)


def start_terminal_client(host, port, username):
    """Run the text-based client."""
    client = TerminalChatClient(
        server_host=host,
        server_port=port,
        username=username,
    )
    try:
        client.start()
    except KeyboardInterrupt:
        print("\nDisconnecting...")


def start_gui_client(host, port, username):
    """Run the Tkinter client window."""
    app = ChatClientApp(server_host=host, server_port=port)
    if username:
        app.username_var.set(username)
    app.run()


def main():
    """Start the client in GUI mode or CLI mode."""
    parsed = parse_arguments()
    if parsed is None:
        return

    host, port, username, cli_mode = parsed

    print("=" * 70)
    print("PULSE-CHAT CLIENT")
    print("=" * 70)
    print()

    if cli_mode:
        start_terminal_client(host, port, username)
        return

    gui_ok, gui_error = gui_is_available()
    if gui_ok:
        start_gui_client(host, port, username)
    else:
        print(f"[CLIENT] GUI unavailable: {gui_error}")
        print("[CLIENT] Falling back to terminal mode.")
        try:
            start_terminal_client(host, port, username)
        except EOFError:
            print("[CLIENT] No interactive input available for terminal mode.")
        except Exception as error:
            print(f"[CLIENT] Terminal client failed: {error}")


if __name__ == "__main__":
    main()
