import os
from dotenv import load_dotenv
import psycopg2


load_dotenv()
# Подключаемся к базе данных PostgreSQL

# Функция для подключения к базе данных и регистрации пользователя
async def register_user(telegram_id, username, first_name):
    try:
        conn = psycopg2.connect(os.getenv("LINK"))
        print("Подключение установлено успешно.")

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
        print(f"Ошибка подключения: {e}")
        exit()

