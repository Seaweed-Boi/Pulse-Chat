"""
Chat Client Module

This module implements the chat client that:
1. Connects to the server over TLS
2. Sends messages typed by the user
3. Receives and displays messages from other users
4. Handles the connection lifecycle

Key Networking Concepts:
- TCP Client Socket: Initiates connection to server
- SSL/TLS Client: Validates server certificate, encrypts traffic
- Threading: Separate thread for receiving messages (allows concurrent send/receive)
- Non-blocking I/O: User can type while receiving messages
"""

import socket
import ssl
import threading
import sys
from utils.message_protocol import MessageProtocol


class ChatClient:
    """
    Secure chat client that connects to the chat server via TLS.
    """
    
    def __init__(
        self,
        server_host: str = 'localhost',
        server_port: int = 5555,
        username: str = None
    ):
        """
        Initialize the chat client.
        
        Args:
            server_host: Hostname or IP address of the chat server
            server_port: Port number the server is listening on
            username: Username for this client
        """
        self.server_host = server_host
        self.server_port = server_port
        self.username = username or self._get_username()
        
        self.socket = None
        self.running = False
        self.receive_thread = None
    
    def _get_username(self) -> str:
        """Prompt user for their username."""
        username = input("Enter your username: ").strip()
        while not username:
            username = input("Username cannot be empty. Try again: ").strip()
        return username
    
    def connect(self):
        """
        Connect to the chat server using TLS.
        
        Process:
        1. Create a TCP socket
        2. Create an SSL context with certificate verification disabled
           (since we're using self-signed certs)
        3. Wrap the socket with SSL
        4. Connect to the server (TLS handshake occurs here)
        5. Send join message with username
        """
        try:
            # Step 1: Create a TCP socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Step 2: Create SSL context for the client
            # We use PROTOCOL_TLS_CLIENT which enforces certificate checking by default
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # For self-signed certificates, we need to disable certificate verification
            # In production, you would load the CA certificate and verify properly
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Step 3: Wrap the socket with SSL
            self.socket = ssl_context.wrap_socket(
                client_socket,
                server_hostname=self.server_host
            )
            
            # Step 4: Connect to the server
            # The TLS handshake happens here automatically
            print(f"[CLIENT] Connecting to {self.server_host}:{self.server_port}...")
            self.socket.connect((self.server_host, self.server_port))
            print(f"[CLIENT] Secure connection established!")
            print(f"[CLIENT] Using cipher: {self.socket.cipher()}\n")
            
            # Step 5: Send join message
            join_message = MessageProtocol.create_message(
                MessageProtocol.TYPE_JOIN,
                self.username,
                f"{self.username} joined"
            )
            self._send_message(join_message)
            
            self.running = True
            return True
        
        except ConnectionRefusedError:
            print("[CLIENT] Error: Could not connect to server. Is it running?")
            return False
        except ssl.SSLError as e:
            print(f"[CLIENT] SSL Error: {e}")
            return False
        except Exception as e:
            print(f"[CLIENT] Connection error: {e}")
            return False
    
    def _send_message(self, message: dict):
        """
        Send a message to the server.
        
        Args:
            message: Message dictionary to send
        """
        try:
            encoded = MessageProtocol.encode_message(message)
            self.socket.sendall(encoded)
        except Exception as e:
            print(f"[CLIENT] Error sending message: {e}")
            self.running = False
    
    def _receive_messages(self):
        """
        Continuously receive messages from the server.
        Runs in a separate thread to allow simultaneous send/receive.
        """
        try:
            # Create a file-like object for line-based reading
            server_file = self.socket.makefile('rb')
            
            while self.running:
                # Read one line (one message) from the server
                data = server_file.readline()
                
                if not data:
                    # Server disconnected
                    print("\n[CLIENT] Disconnected from server")
                    self.running = False
                    break
                
                # Decode and display the message
                message = MessageProtocol.decode_message(data)
                if message:
                    # Format and display the message
                    display_text = MessageProtocol.format_display_message(message)
                    print(display_text)
        
        except ConnectionResetError:
            print("\n[CLIENT] Connection lost")
            self.running = False
        except Exception as e:
            if self.running:
                print(f"\n[CLIENT] Error receiving messages: {e}")
            self.running = False
    
    def start(self):
        """
        Start the client's main loop.
        
        Creates a separate thread for receiving messages, then handles
        user input in the main thread.
        """
        if not self.connect():
            return
        
        # Start the receive thread
        self.receive_thread = threading.Thread(
            target=self._receive_messages,
            daemon=True
        )
        self.receive_thread.start()
        
        # Display usage instructions
        print("=" * 60)
        print("Connected to Pulse-Chat!")
        print("Type your messages and press Enter to send.")
        print("Type '/quit' to exit.")
        print("=" * 60)
        print()
        
        # Main loop - handle user input
        try:
            while self.running:
                try:
                    # Read user input
                    user_input = input()
                    
                    if not self.running:
                        break
                    
                    # Handle special commands
                    if user_input.lower() == '/quit':
                        break
                    
                    if user_input.strip():
                        # Create and send chat message
                        chat_message = MessageProtocol.create_message(
                            MessageProtocol.TYPE_CHAT,
                            self.username,
                            user_input
                        )
                        self._send_message(chat_message)
                
                except EOFError:
                    # Handle Ctrl+D
                    break
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    break
        
        finally:
            self.disconnect()
    
    def disconnect(self):
        """
        Disconnect from the server and clean up resources.
        """
        if self.running:
            # Send leave message
            leave_message = MessageProtocol.create_message(
                MessageProtocol.TYPE_LEAVE,
                self.username,
                f"{self.username} left"
            )
            self._send_message(leave_message)
        
        self.running = False
        
        # Close the socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("\n[CLIENT] Disconnected")


if __name__ == "__main__":
    # Allow running this module directly
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
    username = sys.argv[3] if len(sys.argv) > 3 else None
    
    client = ChatClient(host, port, username)
    client.start()
