import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor


load_dotenv()

# Функция для подключения к базе данных и регистрации пользователя
async def register_user(telegram_id, username, first_name):
    try:
        conn = psycopg2.connect(os.getenv("LINK"))
        cursor = conn.cursor()

        # Проверяем, зарегистрирован ли уже пользователь
        cursor.execute("SELECT 1 FROM users WHERE telegram_id = %s", (telegram_id,))
        existing_user = cursor.fetchone()  # Получаем одну строку результата
        if existing_user:
            return False  # Пользователь уже существует

        # Если не существует, добавляем нового пользователя
        cursor.execute("""
                    INSERT INTO users (telegram_id, username, first_name, create_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP);
                """, (telegram_id, username, first_name))

        # Подтверждаем транзакцию
        conn.commit()

        return True

    except Exception as e:
        print(f"Error 1: {e}")
        exit()

# Функция для добавления клиента в БД
async def add_client_to_db(businessman_id, name, phone, notes):
    try:
        conn = psycopg2.connect(os.getenv("LINK"))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clients (businessman_id, name, phone, notes, create_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (businessman_id, name, phone, notes))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error 2: {e}")
        return False


# Функция для асинхронного подключения и получения клиентов с пагинацией
async def get_clients_from_db(businessman_id):
    try:
        conn = psycopg2.connect(os.getenv("LINK"))
        cursor = conn.cursor()

        # Запрос с пагинацией
        query = """
        SELECT name, phone, notes
        FROM clients
        WHERE businessman_id = %s
        ORDER BY create_at DESC
        """
        cursor.execute(query, (businessman_id,))

        clients = cursor.fetchall()
        cursor.close()
        conn.close()
        return clients
    except Exception as e:
        print(f"Error 3: {e}")
        return []

async def delete_clients_from_db(businessman_id):
    try:
        conn = psycopg2.connect(os.getenv("LINK"))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM clients WHERE businessman_id = %s;", (businessman_id,))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error 4: {e}")
        return []

async def get_ids_from_db(businessman_id):
    try:
        conn = psycopg2.connect(os.getenv("LINK"))
        cursor = conn.cursor()

        query = """
                SELECT id
                FROM clients
                WHERE businessman_id = %s
                ORDER BY create_at DESC
                """
        cursor.execute(query, (businessman_id,))
        client_ids = [row[0] for row in cursor.fetchall()]
        conn.commit()
        cursor.close()
        conn.close()
        return client_ids
    except Exception as e:
        print(f"Error 4: {e}")
        return []