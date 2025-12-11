import streamlit as st
import socket
import time
from streamlit_autorefresh import st_autorefresh

# --- Configuration ---
UDP_PORT = 9002
TCP_PORT = 9001
BUFFER_SIZE = 4096

# --- Helper Functions ---

def find_server_udp():
    """Broadcasts on UDP to find the server's IP."""
    st.write("Searching for chat server via UDP broadcast...")
    discover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    discover_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    discover_socket.settimeout(3.0)
    
    try:
        discover_socket.sendto(b"DISCOVER_CHAT_SERVER", ('<broadcast>', UDP_PORT))
        data, addr = discover_socket.recvfrom(BUFFER_SIZE)
        if data == b"CHAT_SERVER_FOUND":
            st.session_state.server_ip = addr[0]
            st.write(f"Found server at {addr[0]}!")
            return addr[0]
    except socket.timeout:
        st.error("Could not find server. Is server.py running?")
        return None
    finally:
        discover_socket.close()

def connect_to_server(ip, username):
    """Connects to the TCP server and stores socket in session state."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, TCP_PORT))
        # --- CRITICAL ---
        # Set the socket to non-blocking mode.
        # This means s.recv() will return immediately, not wait.
        s.setblocking(False) 
        # ---
        s.send(username.encode('utf-8'))
        
        st.session_state.tcp_socket = s
        st.session_state.status = "connected"
        st.session_state.username = username
        st.session_state.messages = [] # Clear message history
        st.success(f"Connected to {ip} as {username}")
        return True
    except Exception as e:
        st.error(f"Failed to connect to TCP server: {e}")
        return False

def check_for_messages():
    """Polls the non-blocking socket for new messages."""
    if 'tcp_socket' not in st.session_state:
        return

    s = st.session_state.tcp_socket
    try:
        # In non-blocking mode, this loop will run as long
        # as there is data to be read, then raise a
        # BlockingIOError when it's empty.
        while True:
            data = s.recv(BUFFER_SIZE).decode('utf-8')
            if not data:
                # Server gracefully disconnected
                st.session_state.status = "disconnected"
                st.session_state.tcp_socket.close()
                del st.session_state.tcp_socket
                st.warning("Server disconnected.")
                break
            
            # Add all received messages (they might be buffered)
            for msg in data.splitlines():
                st.session_state.messages.append(msg)
                
    except BlockingIOError:
        # This is not an error! It's the expected behavior.
        # It just means "no more messages right now."
        pass
    except ConnectionResetError:
        st.session_state.status = "disconnected"
        st.error("Connection to server was lost.")
        del st.session_state.tcp_socket
    except Exception as e:
        st.error(f"Error receiving message: {e}")
        st.session_state.status = "disconnected"
        del st.session_state.tcp_socket

# --- Main App Logic ---

st.set_page_config(layout="centered", page_title="Chat App")
st.title("Chat Application")
st.markdown("This Streamlit app connects to the `server.py` backend.")

# Initialize session state
if 'status' not in st.session_state:
    st.session_state.status = "disconnected"
    st.session_state.server_ip = None
    st.session_state.username = ""
    st.session_state.messages = []

# --- 1. Disconnected State (Login Screen) ---
if st.session_state.status == "disconnected":
    st.header("Join Chat")
    
    # Try to find server automatically
    if st.session_state.server_ip is None:
        if st.button("Find Server (UDP)"):
            with st.spinner("Broadcasting on network..."):
                find_server_udp()
    
    if st.session_state.server_ip:
        st.success(f"Server found at: {st.session_state.server_ip}")
        st.session_state.username = st.text_input(
            "Enter your username", 
            st.session_state.username
        )
        
        if st.button("Connect (TCP)") and st.session_state.username:
            with st.spinner("Connecting..."):
                if connect_to_server(
                    st.session_state.server_ip, 
                    st.session_state.username
                ):
                    st.rerun() # Rerun to switch to the "connected" view
        elif not st.session_state.username:
            st.info("Please enter a username to connect.")
            
    else:
        st.info("Click 'Find Server' to begin.")

# --- 2. Connected State (Chat Room) ---
elif st.session_state.status == "connected":
    
    # This component makes Streamlit re-run this script every 1000ms (1 sec)
    # This creates our "game loop" to poll for messages.
    st_autorefresh(interval=1000, limit=None, key="chat_refresher")
    
    # On each 1-second refresh, check the socket for new data
    check_for_messages()

    # --- NEW: Chart Logic ---
    with st.sidebar:
        st.header("Chat Activity")
        
        # 1. Process messages to get user counts
        user_counts = {}
        for msg_str in st.session_state.messages:
            if ":" in msg_str:
                try:
                    name, message = msg_str.split(":", 1)
                    if name != "SYSTEM":
                        # Increment count for the user
                        user_counts[name] = user_counts.get(name, 0) + 1
                except Exception:
                    pass # Ignore system or malformed messages

        # 2. Display the chart
        if user_counts:
            st.markdown("### Messages per User")
            # st.bar_chart will use the dictionary keys as x-axis
            # and values as y-axis
            st.bar_chart(user_counts)
        else:
            st.info("No user messages have been sent yet.")
    # --- END: Chart Logic ---

    st.header(f"Chat Room")
    st.caption(f"Connected as: {st.session_state.username} @ {st.session_state.server_ip}")

    # Display messages
    chat_container = st.container(height=400, border=True)
    with chat_container:
        for msg_str in st.session_state.messages:
            if ":" in msg_str:
                try:
                    name, message = msg_str.split(":", 1)
                    
                    # --- MODIFICATION ---
                    # Removed the avatar = "..." line
                    # ---
                    
                    if name == "SYSTEM":
                        st.info(message)
                    else:
                        # Call st.chat_message(name) without the avatar parameter
                        with st.chat_message(name):
                            st.markdown(message)
                except Exception:
                    st.write(msg_str) # Fallback
            else:
                st.write(msg_str) # Fallback for simple messages

    # Send message
    prompt = st.chat_input("Say something...")
    if prompt:
        try:
            # Send the message over the socket
            st.session_state.tcp_socket.send(prompt.encode('utf-8'))
            
            # Add our *own* message to the list immediately
            # The server is set to *not* broadcast back to the sender
            own_message = f"{st.session_state.username}: {prompt}"
            st.session_state.messages.append(own_message)
            
            # Rerun immediately to show the new message
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to send message: {e}")
            st.session_state.status = "disconnected"
            del st.session_state.tcp_socket
            st.rerun()