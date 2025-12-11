# Chat Application using TCP & UDP in Python

This project demonstrates real-time communication using Python’s socket programming. 
It includes a TCP chat server, UDP discovery server, a terminal-based client, and a 
Streamlit-based web chat interface.

---

## 🚀 Features

- **UDP Server Discovery** – Clients automatically find the chat server.
- **TCP Reliable Chat** – Stable message delivery with ordered communication.
- **Multi-Client Support** – Multiple users can chat at the same time.
- **Streamlit Web App** – Real-time chat UI with auto-refresh.
- **Activity Chart** – Live bar chart showing messages per user.
- **Join/Leave Alerts** – Server broadcasts system notifications.

---

## 📂 Project Structure

```
├── server.py          # TCP + UDP server
├── client.py          # Terminal chat client
├── app.py             # Streamlit web chat interface
├── requirements.txt   # Required libraries
└── README.md
```

---

## 🛠 Installation

### 1. Download the project
Extract or clone the project folder.

### 2. Install dependencies
```
pip install -r requirements.txt
```

---

## ▶️ How to Run

### **Step 1: Start the Server**
```
python server.py
```

### **Step 2A: Run the Terminal Client**
```
python client.py
```

### **Step 2B: Run the Streamlit Web App**
```
streamlit run app.py
```

---

## 📡 How It Works

- The client broadcasts a **UDP DISCOVER** message.
- The server responds with **CHAT_SERVER_FOUND**.
- The client then connects to the server using **TCP**.
- Messages are exchanged and broadcast to all connected users.

---

## 📘 Technologies Used

- Python (socket, threading)
- Streamlit
- streamlit-autorefresh
- Pandas

---

## 📌 Notes

- Ensure server and client are on the **same network**.
- Use **Ctrl + C** to stop the server.
- Type `exit` in the terminal client to disconnect.

---

## ✨ Future Enhancements

- GUI-based desktop client
- Message encryption (TLS/SSL)
- File sharing
- Group chat rooms

---

## 👥 Contributors

- Kishore  
- Shafiya  
- Shaik Samreen  
- Sohan Jwaliya Kasa  
- Syed Naseera  

