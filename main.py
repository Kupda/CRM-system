import os
from dotenv import load_dotenv
import psycopg2
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from db import register_user, add_client_to_db

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


user_data = {}
@dp.message(Command("add_client"))
async def cmd_add_client(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("Введите имя клиента:")


@dp.message()
async def process_message(message: types.Message):
    user_id = message.from_user.id

    # Если пользователь еще не начал регистрацию — игнорируем
    if user_id not in user_data:
        return

    user_step = len(user_data[user_id])  # Определяем, на каком шаге он

    if user_step == 0:  # Имя
        user_data[user_id]["name"] = message.text
        await message.answer("Введите номер телефона клиента (пример: +79123456789):")

    elif user_step == 1:  # Номер телефона
        phone = message.text.strip()
        user_data[user_id]["phone"] = phone
        await message.answer("Введите заметку о клиенте (или '-' если нет):")

    elif user_step == 2:  # Заметка
        user_data[user_id]["notes"] = None if message.text == "-" else message.text
        # Достаем данные
        data = user_data.pop(user_id)
        success = await add_client_to_db(
            businessman_id=user_id,
            name=data["name"],
            phone=data["phone"],
            notes=data["notes"]
        )
        if success:
            await message.answer("Клиент успешно добавлен в базу данных!")
        else:
            await message.answer("Ошибка при добавлении клиента. Попробуйте ещё раз.")


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())