import mysql.connector
from mysql.connector import Error

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