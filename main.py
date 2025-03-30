import os
from dotenv import load_dotenv
import psycopg2
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import register_user, add_client_to_db

# Считываем токен из файла .env
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Диспетчер
dp = Dispatcher()
router = Router()
storage = MemoryStorage()
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
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    telegram_id = user.id
    username = user.username
    first_name = user.first_name

    if await register_user(telegram_id, username, first_name):
        await message.reply(f"Привет, {first_name}! Ты успешно зарегистрирован в базе данных.")
    else:
        await message.reply(f"Привет, {first_name}! Ты уже зарегистрирован в базе данных.")


class ClientStates(StatesGroup):
    name = State()  # Имя клиента
    phone = State()  # Телефон клиента
    notes = State()  # Заметки клиента


# Команда /add_client для добавления нового клиента
@router.message(Command("add_client"))
async def cmd_add_client(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, введите имя клиента.")
    await state.set_state(ClientStates.name)


# Обработка ввода имени клиента
@router.message(ClientStates.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)
    await message.answer("Теперь введите телефон клиента.")
    await state.set_state(ClientStates.phone)


# Обработка ввода телефона клиента
@router.message(ClientStates.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)
    await message.answer("Теперь введите заметку о клиенте.")
    await state.set_state(ClientStates.notes)


# Обработка ввода заметки о клиенте
@router.message(ClientStates.notes)
async def process_notes(message: types.Message, state: FSMContext):
    notes = message.text
    user_data = await state.get_data()

    name = user_data["name"]
    phone = user_data["phone"]

    # Получаем ID бизнесмена
    businessman_id = message.from_user.id

    # Добавляем клиента в базу данных
    success = await add_client_to_db(businessman_id, name, phone, notes)

    if success:
        await message.answer(f"Клиент {name} добавлен успешно!")
    else:
        await message.answer("Произошла ошибка при добавлении клиента.")

    await state.clear()

# Запуск процесса поллинга новых апдейтов
async def main():
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())