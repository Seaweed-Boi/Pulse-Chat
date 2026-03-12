"""
Client Handler Module

This module handles individual client connections in separate threads.
Each connected client gets its own ClientHandler instance running in its own thread,
allowing the server to handle multiple clients concurrently.

Key Networking Concepts:
- Threading: Each client runs in a separate thread for concurrent handling
- Buffered Reading: Messages are read line-by-line using makefile()
- Exception Handling: Graceful handling of disconnections and errors
"""

import threading
import ssl
from typing import Callable, Optional
from utils.message_protocol import MessageProtocol


class ClientHandler:
    """
    Handles communication with a single connected client.
    Runs in a separate thread to allow concurrent client handling.
    """
    
    def __init__(
        self,
        client_socket: ssl.SSLSocket,
        client_address: tuple,
        broadcast_callback: Callable,
        remove_callback: Callable
    ):
        """
        Initialize the client handler.
        
        Args:
            client_socket: The secure SSL-wrapped socket for this client
            client_address: Tuple of (ip_address, port) for the client
            broadcast_callback: Function to call to broadcast messages to all clients
            remove_callback: Function to call when this client disconnects
        """
        self.socket = client_socket
        self.address = client_address
        self.broadcast = broadcast_callback
        self.remove_client = remove_callback
        self.username: Optional[str] = None
        self.running = True
        
        # Create a thread for this client
        self.thread = threading.Thread(target=self.handle_client, daemon=True)
    
    def start(self):
        """Start the client handler thread."""
        self.thread.start()
    
    def handle_client(self):
        """
        Main loop for handling client communication.
        This runs in a separate thread for each client.
        
        Process:
        1. Wait for username from client
        2. Announce client join to all users
        3. Loop: receive messages and broadcast them
        4. Handle disconnection gracefully
        """
        try:
            # Use makefile() to create a file-like object for line-based reading
            # This simplifies receiving messages delimited by newlines
            client_file = self.socket.makefile('rb')
            
            # First message should contain the username
            data = client_file.readline()
            if not data:
                return
            
            message = MessageProtocol.decode_message(data)
            if message and message.get("type") == MessageProtocol.TYPE_JOIN:
                self.username = message.get("username", "Unknown")
                print(f"[SERVER] {self.username} connected from {self.address}")
                
                # Broadcast join message to all clients
                join_msg = MessageProtocol.create_message(
                    MessageProtocol.TYPE_JOIN,
                    self.username,
                    f"{self.username} joined the chat"
                )
                self.broadcast(join_msg, exclude=self)
            
            # Main message receiving loop
            while self.running:
                # Read one line (one message) from the client
                data = client_file.readline()
                
                if not data:
                    # Client disconnected
                    break
                
                # Decode and process the message
                message = MessageProtocol.decode_message(data)
                if message:
                    msg_type = message.get("type")
                    
                    if msg_type == MessageProtocol.TYPE_CHAT:
                        # Regular chat message - broadcast to all clients
                        print(f"[{self.username}]: {message.get('content', '')}")
                        self.broadcast(message, exclude=None)
                    
                    elif msg_type == MessageProtocol.TYPE_LEAVE:
                        # Client wants to leave
                        break
        
        except ConnectionResetError:
            print(f"[SERVER] Connection reset by {self.username or self.address}")
        except Exception as e:
            print(f"[SERVER] Error handling client {self.username or self.address}: {e}")
        finally:
            self.cleanup()
    
    def send_message(self, message: dict):
        """
        Send a message to this client.
        
        Args:
            message: Message dictionary to send
        """
        try:
            encoded = MessageProtocol.encode_message(message)
            self.socket.sendall(encoded)
        except Exception as e:
            print(f"[SERVER] Error sending to {self.username}: {e}")
            self.running = False
    
    def cleanup(self):
        """
        Clean up resources when client disconnects.
        This ensures proper resource management and notifies other clients.
        """
        self.running = False
        
        # Announce departure to other clients
        if self.username:
            leave_msg = MessageProtocol.create_message(
                MessageProtocol.TYPE_LEAVE,
                self.username,
                f"{self.username} left the chat"
            )
            self.broadcast(leave_msg, exclude=self)
            print(f"[SERVER] {self.username} disconnected")
        
        # Close the socket
        try:
            self.socket.close()
        except:
            pass
        
        # Remove this client from the server's client list
        self.remove_client(self)
