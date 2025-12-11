# server.py
import socket
import threading

# --- Configuration ---
HOST = '0.0.0.0'  # Listen on all available interfaces
TCP_PORT = 9001
UDP_PORT = 9002
BUFFER_SIZE = 1024

# --- State ---
clients = []  # List to store all connected client (socket, username) tuples
clients_lock = threading.Lock() # Lock to ensure thread-safe access to clients list

def broadcast_message(message, sender_socket):
    """Sends a message to all connected clients except the sender."""
    with clients_lock:
        # We store (socket, username) tuples
        for client_socket, username in clients:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    # Handle broken connections
                    remove_client((client_socket, username))

def remove_client(client_tuple):
    """Removes a client from the active list."""
    if client_tuple in clients:
        clients.remove(client_tuple)

def handle_tcp_client(client_socket, addr):
    """Handles an individual client connection over TCP."""
    print(f"[TCP] New connection from {addr}")
    
    # First message from the client is their username
    try:
        username = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        if not username:
            raise ConnectionError("No username received")
            
        print(f"[TCP] Username set to '{username}' for {addr}")
        
        # Add client to the list
        with clients_lock:
            clients.append((client_socket, username))
            
        # Announce the new user to everyone
        join_msg = f"SYSTEM: {username} has joined the chat."
        print(join_msg)
        broadcast_message(join_msg, client_socket)

        # Main message loop
        while True:
            message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if not message:
                break # Client disconnected
                
            full_message = f"{username}: {message}"
            print(f"[TCP] Received: {full_message}")
            
            # Broadcast the message to all other clients
            broadcast_message(full_message, client_socket)
            
    except ConnectionResetError:
        print(f"[TCP] Connection lost with {username} ({addr})")
    except Exception as e:
        print(f"[TCP] Error with {addr}: {e}")
        
    # --- Cleanup ---
    client_tuple = (client_socket, username if 'username' in locals() else 'Unknown')
    with clients_lock:
        remove_client(client_tuple)
    client_socket.close()
    
    leave_msg = f"SYSTEM: {client_tuple[1]} has left the chat."
    print(leave_msg)
    broadcast_message(leave_msg, None) # Broadcast leave message to all

def start_tcp_server():
    """Starts the main TCP chat server."""
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind((HOST, TCP_PORT))
    tcp_server.listen(5)
    print(f"[*] TCP Chat Server listening on port {TCP_PORT}")

    while True:
        client_socket, addr = tcp_server.accept()
        # Start a new thread for each client
        thread = threading.Thread(target=handle_tcp_client, args=(client_socket, addr))
        thread.daemon = True # Allows server to exit even if threads are running
        thread.start()

def start_udp_server():
    """Starts the UDP discovery server."""
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server.bind((HOST, UDP_PORT))
    print(f"[*] UDP Discovery Server listening on port {UDP_PORT}")

    while True:
        try:
            # Wait for a discovery message
            data, addr = udp_server.recvfrom(BUFFER_SIZE)
            message = data.decode('utf-8')
            
            if message == "DISCOVER_CHAT_SERVER":
                print(f"[UDP] Discovery request from {addr}. Responding.")
                # Respond directly to the client who asked
                udp_server.sendto(b"CHAT_SERVER_FOUND", addr)
        except Exception as e:
            print(f"[UDP] Error: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting server...")
    
    # Start the TCP server in a separate thread
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    # Start the UDP server in a separate thread
    udp_thread = threading.Thread(target=start_udp_server)
    udp_thread.daemon = True
    udp_thread.start()

    # Keep the main thread alive (otherwise the program would exit)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down server...")