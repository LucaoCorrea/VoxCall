import socket
import threading
import tkinter as tk
from tkinter import messagebox

PORT = 12345
SERVER_IP = "127.0.0.1"
BUFFER_SIZE = 1024
clients = {}
server_socket = None
server_running = False


def handle_client(client_socket, addr):
    client_id = f"{addr[0]}:{addr[1]}"
    clients[client_id] = client_socket
    update_client_list()
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            for client in clients.values():
                if client != client_socket:
                    client.sendall(data)
    except:
        pass
    finally:
        if client_id in clients:
            del clients[client_id]
        client_socket.close()
        update_client_list()


def accept_clients():
    global server_socket, server_running
    while server_running:
        try:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
        except:
            break


def start_server():
    global server_socket, server_running
    if not server_running:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SERVER_IP, PORT))
        server_socket.listen(5)
        server_running = True
        threading.Thread(target=accept_clients, daemon=True).start()
        messagebox.showinfo("Server", f"Server started on port {PORT}")
        server_btn.config(text="Stop Server", command=stop_server)
        status_label.config(text="Server On", fg="green")
        update_client_list()


def stop_server():
    global server_socket, server_running
    if server_running:
        server_running = False
        for client in clients.values():
            client.close()
        clients.clear()
        server_socket.close()
        messagebox.showinfo("Server", "Server stopped")
        server_btn.config(text="Start Server", command=start_server)
        status_label.config(text="Server Off", fg="red")
        update_client_list()


def disconnect_client():
    selected_client = client_listbox.get(tk.ACTIVE)
    if selected_client in clients:
        clients[selected_client].close()
        del clients[selected_client]
        update_client_list()


def update_client_list():
    client_listbox.delete(0, tk.END)
    for client in clients.keys():
        client_listbox.insert(tk.END, client)


def create_server_gui():
    global status_label, server_btn, client_listbox
    root = tk.Tk()
    root.title("VoxCall Server")
    root.geometry("400x300")
    
    server_btn = tk.Button(root, text="Start Server", command=start_server)
    server_btn.pack(pady=10)
    
    status_label = tk.Label(root, text="Server Off", fg="red")
    status_label.pack(pady=10)
    
    client_listbox = tk.Listbox(root)
    client_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
    
    disconnect_btn = tk.Button(root, text="Disconnect Client", command=disconnect_client)
    disconnect_btn.pack(pady=5)
    
    root.mainloop()


if __name__ == "__main__":
    create_server_gui()
