import socket
import pyaudio
import threading
import tkinter as tk
from tkinter import messagebox, Label, Frame, Entry, Button, Listbox, Scrollbar
from tkinter import font as tkFont
import random
import string
import sys
import os
from PIL import Image, ImageTk
from io import BytesIO
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import smtplib
from email.mime.text import MIMEText

# Adiciona o diretório pai ao PATH para importar módulos personalizados
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from db.db import store_user_in_mysql, get_messages_from_mysql, add_contact, get_contacts, add_friend_request, get_friend_requests, accept_friend_request
# Configurações
PORT = 12345
SERVER_IP = "127.0.0.1"
BUFFER_SIZE = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 2048

# Variáveis globais
p = pyaudio.PyAudio()
client_socket = None
client_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
mute_audio = False
user_name = "User_" + client_id
profile_pic = ""
dark_mode = False


class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VoxCall - Client")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        self.dark_mode = False

        # Fonte personalizada
        self.custom_font = tkFont.Font(family="Helvetica", size=12)

        # Frame principal
        self.main_frame = Frame(root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Tela de login
        self.create_login_screen()

    def create_login_screen(self):
        """Cria a tela de login."""
        # Limpa o frame principal
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Título
        title_label = Label(
            self.main_frame,
            text="VoxCall",
            font=("Helvetica", 24, "bold"),
            bg="#f0f0f0",
            fg="#333",
        )
        title_label.pack(pady=20)

        # Botão de login com Google
        self.google_login_btn = Button(
            self.main_frame,
            text="Login com Google",
            command=self.authenticate_google,
            font=self.custom_font,
            bg="#4285F4",
            fg="white",
            padx=20,
            pady=10,
        )
        self.google_login_btn.pack(pady=10)

        # Botão de modo noturno
        self.dark_mode_btn = Button(
            self.main_frame,
            text="Modo Noturno",
            command=self.toggle_dark_mode,
            font=self.custom_font,
            bg="#555",
            fg="white",
            padx=20,
            pady=10,
        )
        self.dark_mode_btn.pack(pady=10)

    def create_authenticated_screen(self):
        """Cria a tela após autenticação."""
        # Limpa o frame principal
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Frame superior (perfil e botões)
        top_frame = Frame(self.main_frame, bg=self.get_bg_color())
        top_frame.pack(fill=tk.X, pady=10)

        # Exibir foto de perfil
        if profile_pic:
            try:
                response = requests.get(profile_pic)
                if response.status_code == 200:
                    image_data = response.content
                    image = Image.open(BytesIO(image_data))
                    image = image.resize((50, 50), Image.Resampling.LANCZOS)
                    self.profile_image = ImageTk.PhotoImage(image)
                    profile_label = Label(
                        top_frame, image=self.profile_image, bg=self.get_bg_color()
                    )
                    profile_label.pack(side=tk.LEFT, padx=10)
                else:
                    print(f"Erro ao baixar a imagem: {response.status_code}")
            except Exception as e:
                print(f"Erro ao processar a imagem: {e}")

        # Nome do usuário
        self.profile_name_label = Label(
            top_frame,
            text=user_name,
            font=self.custom_font,
            bg=self.get_bg_color(),
            fg=self.get_fg_color(),
        )
        self.profile_name_label.pack(side=tk.LEFT, padx=10)

        # Botões de controle
        self.connect_btn = Button(
            top_frame,
            text="Conectar ao Servidor",
            command=self.connect_server,
            font=self.custom_font,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5,
        )
        self.connect_btn.pack(side=tk.LEFT, padx=10)

        self.disconnect_btn = Button(
            top_frame,
            text="Desconectar",
            command=self.disconnect_server,
            state=tk.DISABLED,
            font=self.custom_font,
            bg="#F44336",
            fg="white",
            padx=10,
            pady=5,
        )
        self.disconnect_btn.pack(side=tk.LEFT, padx=10)

        self.mute_btn = Button(
            top_frame,
            text="Mutar Microfone",
            command=self.toggle_mute,
            state=tk.DISABLED,
            font=self.custom_font,
            bg="#FF9800",
            fg="white",
            padx=10,
            pady=5,
        )
        self.mute_btn.pack(side=tk.LEFT, padx=10)

        # Frame de contatos
        self.contacts_frame = Frame(self.main_frame, bg=self.get_bg_color())
        self.contacts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.contacts_listbox = Listbox(
            self.contacts_frame, font=self.custom_font, bg="white", fg="black"
        )
        self.contacts_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = Scrollbar(self.contacts_frame, orient=tk.VERTICAL)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.contacts_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.contacts_listbox.yview)

        self.load_contacts()

        # Botão para adicionar contato
        self.add_contact_btn = Button(
            self.main_frame,
            text="Adicionar Contato",
            command=self.add_contact_dialog,
            font=self.custom_font,
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=5,
        )
        self.add_contact_btn.pack(pady=10)

    def load_contacts(self):
        """Carrega a lista de contatos."""
        contacts = get_contacts(user_name)
        self.contacts_listbox.delete(0, tk.END)
        for contact in contacts:
            self.contacts_listbox.insert(tk.END, contact)

    def add_contact_dialog(self):
        """Exibe um diálogo para adicionar um contato."""
        self.add_contact_window = tk.Toplevel(self.root)
        self.add_contact_window.title("Adicionar Contato")
        self.add_contact_window.geometry("300x150")

        Label(self.add_contact_window, text="E-mail do Contato:").pack(pady=10)
        self.contact_email_entry = Entry(self.add_contact_window, width=30)
        self.contact_email_entry.pack(pady=10)

        Button(
            self.add_contact_window,
            text="Enviar Convite",
            command=self.send_friend_request,
        ).pack(pady=10)

    def send_friend_request(self):
        """Envia um convite de amizade."""
        email = self.contact_email_entry.get()
        if email:
            try:
                add_friend_request(user_name, email)
                self.send_email(email, user_name)
                messagebox.showinfo("Sucesso", "Convite enviado com sucesso!")
                self.add_contact_window.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao enviar convite: {e}")
        else:
            messagebox.showwarning("Aviso", "Por favor, insira um e-mail válido.")

    def send_email(self, to_email, from_user):
        """Envia um e-mail de convite de amizade."""
        subject = "Convite de Amizade no VoxCall"
        body = f"Olá,\n\n{from_user} enviou um convite de amizade para você no VoxCall.\n\nAceite o convite e comece a conversar!\n\nAtenciosamente,\nEquipe VoxCall"

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = "voxcall@example.com"
        msg['To'] = to_email

        try:
            with smtplib.SMTP('localhost') as server:
                server.sendmail("voxcall@example.com", [to_email], msg.as_string())
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")

    def toggle_dark_mode(self):
        """Alterna entre modo claro e escuro."""
        self.dark_mode = not self.dark_mode
        self.update_theme()

    def update_theme(self):
        """Atualiza o tema da interface."""
        bg_color = self.get_bg_color()
        fg_color = self.get_fg_color()
        self.main_frame.configure(bg=bg_color)
        if hasattr(self, "profile_name_label"):
            self.profile_name_label.configure(bg=bg_color, fg=fg_color)
        if hasattr(self, "contacts_listbox"):
            self.contacts_listbox.configure(bg=bg_color, fg=fg_color)
        if hasattr(self, "contacts_frame"):
            self.contacts_frame.configure(bg=bg_color)

    def get_bg_color(self):
        """Retorna a cor de fundo com base no modo."""
        return "#2c2c2c" if self.dark_mode else "#f0f0f0"

    def get_fg_color(self):
        """Retorna a cor do texto com base no modo."""
        return "#ffffff" if self.dark_mode else "#000000"

    def authenticate_google(self):
        """Autentica o usuário com o Google."""
        global user_name, profile_pic
        try:
            credentials_path = os.path.join(
                os.path.dirname(__file__), "client_secrets.json"
            )
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                scopes=[
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "openid",
                ],
            )
            credentials = flow.run_local_server(port=0)
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            user_name = user_info.get("name", "Unknown")
            profile_pic = user_info.get("picture", "")
            self.create_authenticated_screen()
            messagebox.showinfo(
                "Google Login", f"Login bem-sucedido!\nUsuário: {user_name}"
            )
        except FileNotFoundError:
            messagebox.showerror("Erro", "Arquivo client_secrets.json não encontrado!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na autenticação: {e}")

    def connect_server(self):
        """Conecta ao servidor."""
        global client_socket
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, PORT))
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.mute_btn.config(state=tk.NORMAL)
            self.running = True
            self.audio_thread = threading.Thread(target=self.audio_stream)
            self.audio_thread.start()
            messagebox.showinfo("Client", f"Connected to server as {client_id}")
        except (ConnectionError, OSError) as e:
            messagebox.showerror("Error", f"Connection error: {e}")

    def disconnect_server(self):
        """Desconecta do servidor."""
        global client_socket
        if client_socket:
            self.running = False
            client_socket.close()
            client_socket = None
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.mute_btn.config(state=tk.DISABLED)
            messagebox.showinfo("Client", "Disconnected from server")

    def toggle_mute(self):
        """Alterna o estado do microfone."""
        global mute_audio
        mute_audio = not mute_audio
        self.mute_btn.config(
            text="Desmutar Microfone" if mute_audio else "Mutar Microfone"
        )

    def send_message(self):
        """Envia uma mensagem para o servidor."""
        message = self.message_entry.get()
        if message and client_socket:
            try:
                client_socket.send(message.encode())
                self.chat_label.config(
                    text=self.chat_label.cget("text") + f"{user_name}: {message}\n"
                )
                self.message_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send message: {e}")

    def audio_stream(self):
        """Stream de áudio para o servidor."""
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        while self.running:
            if not mute_audio:
                data = stream.read(CHUNK)
                if client_socket:
                    try:
                        client_socket.send(data)
                    except Exception as e:
                        print(f"Error sending audio: {e}")
                        break
        stream.stop_stream()
        stream.close()


if __name__ == "__main__":
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()