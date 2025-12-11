# client.py
import socket
import threading
import sys

# --- Configuration ---
UDP_PORT = 9002
TCP_PORT = 9001
BUFFER_SIZE = 1024
SERVER_IP = None

def find_server_udp():
    """Broadcasts on UDP to find the server's IP."""
    global SERVER_IP
    print("Searching for chat server...")
    
    # Create a UDP socket
    discover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Enable broadcasting
    discover_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Set a timeout so it doesn't wait forever
    discover_socket.settimeout(5.0)

    try:
        # Send the discovery broadcast message
        # '<broadcast>' is a special address for 255.255.255.255
        discover_socket.sendto(b"DISCOVER_CHAT_SERVER", ('<broadcast>', UDP_PORT))
        
        # Wait for a response
        data, addr = discover_socket.recvfrom(BUFFER_SIZE)
        
        if data == b"CHAT_SERVER_FOUND":
            SERVER_IP = addr[0] # The server's IP
            print(f"Found server at {SERVER_IP}!")
            return True
            
    except socket.timeout:
        print("Could not find server. Is it running on the network?")
        return False
    except Exception as e:
        print(f"Error during discovery: {e}")
        return False
    finally:
        discover_socket.close()

def receive_messages(tcp_socket):
    """Listens for incoming messages from the server."""
    while True:
        try:
            message = tcp_socket.recv(BUFFER_SIZE).decode('utf-8')
            if not message:
                print("Connection to server lost.")
                break
            
            # Print the message
            # Use \r to move cursor to start of line to avoid clobbering user input
            sys.stdout.write('\r' + ' ' * 20 + '\r') # Clear the "You: " line
            print(message)
            sys.stdout.write("You: ")
            sys.stdout.flush()

        except ConnectionResetError:
            print("Connection to server was reset.")
            break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    tcp_socket.close()

def send_messages(tcp_socket, username):
    """Handles sending user input to the server."""
    # First, send the username
    try:
        tcp_socket.send(username.encode('utf-8'))
    except Exception as e:
        print(f"Failed to send username: {e}")
        return

    # Then, start the message loop
    while True:
        try:
            sys.stdout.write("You: ")
            sys.stdout.flush()
            message = input()
            
            if message:
                tcp_socket.send(message.encode('utf-8'))
            if message.lower() == 'exit':
                break
        except EOFError: # Happens if input is redirected
            break
        except Exception as e:
            print(f"Error sending message: {e}")
            break
    tcp_socket.close()

# --- Main Execution ---
if __name__ == "__main__":
    if find_server_udp():
        # Server was found, now connect via TCP
        try:
            username = input("Enter your username: ")
            
            # Create the main TCP socket
            chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            chat_socket.connect((SERVER_IP, TCP_PORT))
            print(f"Connected to chat server at {SERVER_IP}:{TCP_PORT}")

            # Start a thread to receive messages
            recv_thread = threading.Thread(target=receive_messages, args=(chat_socket,))
            recv_thread.daemon = True
            recv_thread.start()

            # Start the send loop in the main thread
            # This will block until the user types 'exit' or the connection breaks
            send_messages(chat_socket, username)

        except ConnectionRefusedError:
            print("Connection failed. Is the server's TCP port open?")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("Disconnected.")