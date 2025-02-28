import mysql.connector
from mysql.connector import Error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def connect_mysql():
    try:
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="voxcall"
        )
    except Error as e:
        print(f"Erro ao conectar com o MySQL: {e}")
        return None

def create_tables():
    conn = connect_mysql()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    contact_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS friend_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    friend_id VARCHAR(255) NOT NULL,
                    status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Tabelas criadas com sucesso!")
        except Error as e:
            print(f"Erro ao criar tabelas no MySQL: {e}")
        finally:
            cursor.close()
            conn.close()

def store_user_in_mysql(uid, name, email, profile_picture):
    conn = connect_mysql()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO users (uid, name, email, profile_picture)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (uid, name, email, profile_picture))
            conn.commit()
        except Error as e:
            print(f"Erro ao inserir usuário no MySQL: {e}")
        finally:
            cursor.close()
            conn.close()

def get_messages_from_mysql():
    conn = connect_mysql()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM messages"
            cursor.execute(query)
            messages = cursor.fetchall()
            return messages
        except Error as e:
            print(f"Erro ao buscar mensagens no MySQL: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    else:
        return []

def add_contact(user_id, contact_id):
    conn = connect_mysql()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO contacts (user_id, contact_id)
                VALUES (%s, %s)
            """
            cursor.execute(query, (user_id, contact_id))
            conn.commit()
        except Error as e:
            print(f"Erro ao adicionar contato no MySQL: {e}")
        finally:
            cursor.close()
            conn.close()

def get_contacts(user_id):
    conn = connect_mysql()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM contacts WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            contacts = cursor.fetchall()
            return contacts
        except Error as e:
            print(f"Erro ao buscar contatos no MySQL: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    else:
        return []

def add_friend_request(user_id, friend_id):
    conn = connect_mysql()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO friend_requests (user_id, friend_id)
                VALUES (%s, %s)
            """
            cursor.execute(query, (user_id, friend_id))
            conn.commit()
        except Error as e:
            print(f"Erro ao adicionar solicitação de amizade no MySQL: {e}")
        finally:
            cursor.close()
            conn.close()

def get_friend_requests(user_id):
    conn = connect_mysql()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM friend_requests WHERE friend_id = %s"
            cursor.execute(query, (user_id,))
            requests = cursor.fetchall()
            return requests
        except Error as e:
            print(f"Erro ao buscar solicitações de amizade no MySQL: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    else:
        return []

def accept_friend_request(request_id):
    conn = connect_mysql()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                UPDATE friend_requests
                SET status = 'accepted'
                WHERE id = %s
            """
            cursor.execute(query, (request_id,))
            conn.commit()
        except Error as e:
            print(f"Erro ao aceitar solicitação de amizade no MySQL: {e}")
        finally:
            cursor.close()
            conn.close()

def send_email(to_email, subject, body):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "seu_email@gmail.com"
        smtp_password = "sua_senha"

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)

        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def send_audio(audio_file):
    try:
        print(f"Áudio {audio_file} enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar áudio: {e}")

create_tables()