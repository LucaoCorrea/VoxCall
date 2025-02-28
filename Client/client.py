import socket
import pyaudio
import threading
import tkinter as tk
from tkinter import messagebox, Label, Frame, Entry, Button, Scrollbar, Text
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

PORT = 12345
SERVER_IP = "127.0.0.1"
BUFFER_SIZE = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

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

        self.custom_font = tkFont.Font(family="Helvetica", size=12)

        self.main_frame = Frame(root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_login_screen()

    def create_login_screen(self):
        """Cria a tela de login."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        title_label = Label(
            self.main_frame,
            text="VoxCall",
            font=("Helvetica", 24, "bold"),
            bg="#f0f0f0",
            fg="#333",
        )
        title_label.pack(pady=20)

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


        self.anonymous_login_btn = Button(
            self.main_frame,
            text="Entrar como Anônimo",
            command=self.anonymous_login,
            font=self.custom_font,
            bg="#555",
            fg="white",
            padx=20,
            pady=10,
        )
        self.anonymous_login_btn.pack(pady=10)

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

    def anonymous_login(self):
        """Entra como usuário anônimo."""
        global user_name
        user_name = "Anônimo_" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=4)
        )
        self.create_authenticated_screen()
        messagebox.showinfo("Anônimo", f"Entrou como {user_name}")

    def create_authenticated_screen(self):
        """Cria a tela após autenticação."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        top_frame = Frame(self.main_frame, bg=self.get_bg_color())
        top_frame.pack(fill=tk.X, pady=10)

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

        self.profile_name_label = Label(
            top_frame,
            text=user_name,
            font=self.custom_font,
            bg=self.get_bg_color(),
            fg=self.get_fg_color(),
        )
        self.profile_name_label.pack(side=tk.LEFT, padx=10)

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

        self.chat_frame = Frame(self.main_frame, bg=self.get_bg_color())
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_text = Text(
            self.chat_frame,
            font=self.custom_font,
            bg="white",
            fg="black",
            wrap=tk.WORD,
        )
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = Scrollbar(self.chat_frame, command=self.chat_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.config(yscrollcommand=scrollbar.set)

        self.message_entry = Entry(self.main_frame, font=self.custom_font, width=50)
        self.message_entry.pack(side=tk.LEFT, padx=10, pady=10)

        self.send_msg_btn = Button(
            self.main_frame,
            text="Enviar",
            command=self.send_message,
            font=self.custom_font,
            bg="#2196F3",
            fg="white",
            padx=10,
            pady=5,
        )
        self.send_msg_btn.pack(side=tk.LEFT, pady=10)

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
        if hasattr(self, "chat_text"):
            self.chat_text.configure(bg=bg_color, fg=fg_color)

    def get_bg_color(self):
        """Retorna a cor de fundo com base no modo."""
        return "#2c2c2c" if self.dark_mode else "#f0f0f0"

    def get_fg_color(self):
        """Retorna a cor do texto com base no modo."""
        return "#ffffff" if self.dark_mode else "#000000"

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
            self.receive_thread = threading.Thread(target=self.receive_data)
            self.receive_thread.start()
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
                client_socket.send(f"MSG:{user_name}:{message}".encode())
                self.chat_text.insert(tk.END, f"{user_name}: {message}\n")
                self.message_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send message: {e}")

    def receive_data(self):
        """Recebe dados do servidor (mensagens e áudio)."""
        while self.running:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                if data.startswith(b"MSG:"):
                    message = data.decode("utf-8")
                    _, sender, content = message.split(":", 2)
                    self.chat_text.insert(tk.END, f"{sender}: {content}\n")
                elif data.startswith(b"AUDIO:"):
                    audio_data = data[6:]
                    self.play_audio(audio_data)
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

    def play_audio(self, audio_data):
        """Reproduz os dados de áudio recebidos."""
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
        )
        stream.write(audio_data)
        stream.stop_stream()
        stream.close()

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
                        client_socket.send(b"AUDIO:" + data)
                    except Exception as e:
                        print(f"Error sending audio: {e}")
                        break
        stream.stop_stream()
        stream.close()


if __name__ == "__main__":
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()
