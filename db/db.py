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
