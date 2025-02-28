import socket
import threading
import tkinter as tk
from tkinter import messagebox

PORT = 12345
SERVER_IP = "127.0.0.1"
BUFFER_SIZE = 4096
clients = {}
server_socket = None
server_running = False


def handle_client(client_socket, addr):
    """Lida com a conexão de um cliente."""
    client_id = f"{addr[0]}:{addr[1]}"
    clients[client_id] = client_socket
    update_client_list()
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break

            if data.startswith(b"MSG:"):
                for client in clients.values():
                    if client != client_socket:
                        client.sendall(data)
            elif data.startswith(b"AUDIO:"):
                for client in clients.values():
                    if client != client_socket:
                        client.sendall(data)
    except Exception as e:
        print(f"Erro ao lidar com o cliente {client_id}: {e}")
    finally:
        if client_id in clients:
            del clients[client_id]
        client_socket.close()
        update_client_list()


def accept_clients():
    """Aceita novas conexões de clientes."""
    global server_socket, server_running
    while server_running:
        try:
            client_socket, addr = server_socket.accept()
            threading.Thread(
                target=handle_client, args=(client_socket, addr), daemon=True
            ).start()
        except Exception as e:
            if server_running:
                print(f"Erro ao aceitar cliente: {e}")
            break


def start_server():
    """Inicia o servidor."""
    global server_socket, server_running
    if not server_running:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((SERVER_IP, PORT))
            server_socket.listen(5)
            server_running = True
            threading.Thread(target=accept_clients, daemon=True).start()
            messagebox.showinfo("Server", f"Servidor iniciado na porta {PORT}")
            server_btn.config(text="Parar Servidor", command=stop_server)
            status_label.config(text="Servidor Ligado", fg="green")
            update_client_list()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar o servidor: {e}")


def stop_server():
    """Para o servidor."""
    global server_socket, server_running
    if server_running:
        server_running = False
        for client in clients.values():
            client.close()
        clients.clear()
        server_socket.close()
        messagebox.showinfo("Server", "Servidor parado")
        server_btn.config(text="Iniciar Servidor", command=start_server)
        status_label.config(text="Servidor Desligado", fg="red")
        update_client_list()


def disconnect_client():
    """Desconecta um cliente selecionado."""
    selected_client = client_listbox.get(tk.ACTIVE)
    if selected_client in clients:
        clients[selected_client].close()
        del clients[selected_client]
        update_client_list()


def update_client_list():
    """Atualiza a lista de clientes na interface gráfica."""
    client_listbox.delete(0, tk.END)
    for client in clients.keys():
        client_listbox.insert(tk.END, client)


def create_server_gui():
    """Cria a interface gráfica do servidor."""
    global status_label, server_btn, client_listbox
    root = tk.Tk()
    root.title("VoxCall Server")
    root.geometry("400x300")

    server_btn = tk.Button(root, text="Iniciar Servidor", command=start_server)
    server_btn.pack(pady=10)

    status_label = tk.Label(root, text="Servidor Desligado", fg="red")
    status_label.pack(pady=10)

    client_listbox = tk.Listbox(root)
    client_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

    disconnect_btn = tk.Button(
        root, text="Desconectar Cliente", command=disconnect_client
    )
    disconnect_btn.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    create_server_gui()
