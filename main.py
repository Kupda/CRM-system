import os
from dotenv import load_dotenv
import psycopg2
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from db import register_user

# Считываем токен из файла .env
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Диспетчер
dp = Dispatcher()
# Объект бота
bot = Bot(token=TOKEN)

# Подключаемся к базе данных PostgreSQL
try:
    conn = psycopg2.connect(os.getenv("LINK"))
    print("Подключение установлено успешно.")
except Exception as e:
    print(f"Ошибка подключения: {e}")
    exit()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    telegram_id = user.id
    username = user.username
    first_name = user.first_name

    if await register_user(telegram_id, username, first_name):
        await message.reply(f"Привет, {first_name}! Ты успешно зарегистрирован в базе данных.")
    else:
        await message.reply(f"Привет, {first_name}! Ты уже зарегистрирован в базе данных.")


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())