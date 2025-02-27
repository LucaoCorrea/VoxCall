import socket
import pyaudio
import threading
import tkinter as tk
from tkinter import messagebox
import random
import string
import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from db.db import store_user_in_mysql, get_messages_from_mysql

PORT = 12345
SERVER_IP = "127.0.0.1"
BUFFER_SIZE = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 2048

p = pyaudio.PyAudio()
client_socket = None
client_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
mute_audio = False

def send_audio():
    global mute_audio
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    while client_socket:
        try:
            if not mute_audio:
                data = stream.read(CHUNK, exception_on_overflow=False)
                client_socket.sendall(data)
        except (socket.error, BrokenPipeError):
            break

def receive_audio():
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    while client_socket:
        try:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            stream.write(data)
        except (socket.error, ConnectionResetError):
            break

def send_message(event=None):
    message = message_entry.get()
    if message and client_socket:
        client_socket.sendall(f"MSG:{client_id}: {message}".encode())
        chat_text.insert(tk.END, f"You: {message}\n")
        message_entry.delete(0, tk.END)
        store_user_in_mysql(client_id, "User Name", "user@example.com", "profile_pic.jpg")

def receive_messages():
    while client_socket:
        try:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            data = data.decode(errors="ignore")
            if data.startswith("MSG:"):
                parts = data.split(":", 2)
                sender_id, message = parts[1], parts[2]
                chat_text.insert(tk.END, f"{sender_id}: {message}\n")
                messages = get_messages_from_mysql()
                for msg in messages:
                    chat_text.insert(tk.END, f"{msg['client_id']}: {msg['message']}\n")
            elif data.startswith("UPDATE_USERS:"):
                update_client_list(data[13:].split(","))
        except (socket.error, ConnectionResetError):
            break

def update_client_list(clients):
    client_listbox.delete(0, tk.END)
    for client in clients:
        client_listbox.insert(tk.END, client)

def toggle_mute():
    global mute_audio
    mute_audio = not mute_audio
    mute_btn.config(text="Unmute Microphone" if mute_audio else "Mute Microphone")

def connect_server():
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, PORT))
        messagebox.showinfo("Client", f"Connected to server as {client_id}")
        status_label.config(text=f"Connected (ID: {client_id})", fg="green")
        connect_btn.config(state=tk.DISABLED)
        disconnect_btn.config(state=tk.NORMAL)
        mute_btn.config(state=tk.NORMAL)
        threading.Thread(target=send_audio, daemon=True).start()
        threading.Thread(target=receive_audio, daemon=True).start()
        threading.Thread(target=receive_messages, daemon=True).start()
        client_socket.sendall(f"NEW_CLIENT:{client_id}".encode())
    except (ConnectionError, OSError) as e:
        messagebox.showerror("Error", f"Connection error: {e}")

def disconnect_server():
    global client_socket
    if client_socket:
        client_socket.sendall(f"REMOVE_CLIENT:{client_id}".encode())
        client_socket.close()
        client_socket = None
        messagebox.showinfo("Client", "Disconnected from server")
        status_label.config(text="Disconnected", fg="red")
        connect_btn.config(state=tk.NORMAL)
        disconnect_btn.config(state=tk.DISABLED)
        mute_btn.config(state=tk.DISABLED)

def authenticate_google():
    """Autenticação via Google OAuth2"""
    try:
        credentials_path = os.path.join(os.path.dirname(__file__), "client_secrets.json")
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path,
            scopes=[
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "openid"
            ],
        )
        credentials = flow.run_local_server(port=0)
        messagebox.showinfo("Google Login", "Login bem-sucedido!")
    except FileNotFoundError:
        messagebox.showerror("Erro", "Arquivo client_secrets.json não encontrado!")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha na autenticação: {e}")

def create_client_gui():
    global status_label, connect_btn, disconnect_btn, mute_btn, client_listbox, message_entry, chat_text
    root = tk.Tk()
    root.title("VoxCall - Client")
    root.geometry("800x600")
    
    google_login_btn = tk.Button(root, text="Login com Google", command=authenticate_google)
    google_login_btn.pack(pady=5)
    
    connect_btn = tk.Button(root, text="Conectar ao Servidor", command=connect_server)
    connect_btn.pack(pady=5)
    
    disconnect_btn = tk.Button(root, text="Desconectar", command=disconnect_server, state=tk.DISABLED)
    disconnect_btn.pack(pady=5)
    
    mute_btn = tk.Button(root, text="Mutar Microfone", command=toggle_mute, state=tk.DISABLED)
    mute_btn.pack(pady=5)
    
    status_label = tk.Label(root, text="Desconectado", fg="red")
    status_label.pack(pady=5)
    
    client_listbox = tk.Listbox(root)
    client_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
    
    chat_frame = tk.Frame(root)
    chat_frame.pack(pady=5, fill=tk.BOTH, expand=True)
    
    chat_text = tk.Text(chat_frame, height=10)
    chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = tk.Scrollbar(chat_frame, command=chat_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    chat_text.config(yscrollcommand=scrollbar.set)
    
    message_entry = tk.Entry(root)
    message_entry.pack(pady=5, fill=tk.X, expand=True)
    message_entry.bind("<Return>", send_message)
    
    send_btn = tk.Button(root, text="Enviar", command=send_message)
    send_btn.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    create_client_gui()
