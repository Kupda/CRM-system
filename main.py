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
from db import *

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


# Команда /list_clients
@router.message(Command("list_clients"))
async def cmd_list_clients(message: types.Message):
    global page, clients, max_pages, i, keyboard
    user = message.from_user
    page = 1
    clients = await get_clients_from_db(user.id)
    i = len(clients) + ((page - 1) * 5)
    msg = ""
    if len(clients) == 0:
        await message.answer("У вас нет клиентов")
    else:
        if len(clients) % 5 == 0:
            max_pages = len(clients) / 5
        else:
            max_pages = (len(clients) // 5) + 1
        if max_pages == 1:
            for client in clients:
                name = client[0]
                phone = client[1]
                notes = client[2]
                index = i
                msg += (f"Имя клиента: {name}\n"
                        f"Телефон: {phone}\n"
                        f"Заметка: {notes}\n"
                        f"Номер клиента: {index}\n"
                        f"\n\n")
                i -= 1
        else:
            if (page - 1) * 5 + 4 < len(clients):
                for client in range((page-1)*5, (page-1)*5+5):
                    name = clients[client][0]
                    phone = clients[client][1]
                    notes = clients[client][2]
                    index = i
                    msg += (f"Имя клиента: {name}\n"
                            f"Телефон: {phone}\n"
                            f"Заметка: {notes}\n"
                            f"Номер клиента: {index}\n"
                            f"\n\n")
                    i -= 1
            else:
                for client in range((page-1)*5, len(clients)):
                    name = clients[client][0]
                    phone = clients[client][1]
                    notes = clients[client][2]
                    index = i
                    msg += (f"Имя клиента: {name}\n"
                            f"Телефон: {phone}\n"
                            f"Заметка: {notes}\n"
                            f"Номер клиента: {index}\n"
                            f"\n\n")
                    i -= 1
        keyboard = await pagination_clients(page, max_pages)
        await message.answer(msg, reply_markup=keyboard)


async def pagination_clients(page, max_pages):
    if max_pages == 1:
        return InlineKeyboardMarkup(inline_keyboard=[])
    elif page == 1:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="След. страница", callback_data="next_page")]
            ]
        )
    elif page != 1 and max_pages > page:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Пред. страница", callback_data="prev_page")],
                [InlineKeyboardButton(text="След. страница", callback_data="next_page")]
            ]
        )
    elif page == max_pages:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Пред. страница", callback_data="prev_page")]
            ]
        )


@router.callback_query(lambda c: c.data == "next_page")
async def next_page(callback: types.CallbackQuery):
    global page
    page += 1
    i = len(clients) - ((page-1)*5)
    keyboard = await pagination_clients(page, max_pages)
    msg = ''
    if (page - 1) * 5 + 4 < len(clients):
        for client in range((page - 1) * 5, (page - 1) * 5 + 5):
            name = clients[client][0]
            phone = clients[client][1]
            notes = clients[client][2]
            index = i
            msg += (f"Имя клиента: {name}\n"
                    f"Телефон: {phone}\n"
                    f"Заметка: {notes}\n"
                    f"Номер клиента: {index}\n"
                    f"\n\n")
            i -= 1
    else:
        for client in range((page - 1) * 5, len(clients)):
            name = clients[client][0]
            phone = clients[client][1]
            notes = clients[client][2]
            index = i
            msg += (f"Имя клиента: {name}\n"
                    f"Телефон: {phone}\n"
                    f"Заметка: {notes}\n"
                    f"Номер клиента: {index}\n"
                    f"\n\n")
            i -= 1
    await callback.message.edit_text(msg, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "prev_page")
async def prev_page(callback: types.CallbackQuery):
    global page
    page -= 1
    i = len(clients) - ((page - 1) * 5)
    keyboard = await pagination_clients(page, max_pages)
    msg = ''
    if (page - 1) * 5 + 4 < len(clients):
        for client in range((page - 1) * 5, (page - 1) * 5 + 5):
            name = clients[client][0]
            phone = clients[client][1]
            notes = clients[client][2]
            index = i
            msg += (f"Имя клиента: {name}\n"
                    f"Телефон: {phone}\n"
                    f"Заметка: {notes}\n"
                    f"Номер клиента: {index}\n"
                    f"\n\n")
            i -= 1
    else:
        for client in range((page - 1) * 5, len(clients)):
            name = clients[client][0]
            phone = clients[client][1]
            notes = clients[client][2]
            index = i
            msg += (f"Имя клиента: {name}\n"
                    f"Телефон: {phone}\n"
                    f"Заметка: {notes}\n"
                    f"Номер клиента: {index}\n"
                    f"\n\n")
            i -= 1
    await callback.message.edit_text(msg, reply_markup=keyboard)


# Команда /clear_clients
@router.message(Command("clear_clients"))
async def cmd_clear_clients(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="clear_clients1"),
             InlineKeyboardButton(text="Нет", callback_data="cancel_clear_clients")]
        ]
    )
    await message.answer("Вы уверены, что хотите удалить базу данных всех ваших клиентов?",
                         reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "clear_clients1")
async def clear_clients(callback: types.CallbackQuery):
    businessman_id = callback.from_user.id
    await delete_clients_from_db(businessman_id)
    await callback.message.edit_text("База данных клиентов была очищена")


@router.callback_query(lambda c: c.data == "cancel_clear_clients")
async def cancel_clear_clients(callback: types.CallbackQuery):
    await callback.message.edit_text("Действие отменено")


@router.message(Command("edit_client"))
async def cmd_edit_client(message: types.Message):
    businessman_id = message.from_user.id
    args = message.text.split()  # Разбиваем сообщение на части
    if len(args) < 2:  # Проверяем, есть ли параметр
        await message.reply("Вы не указали параметр! Пример: /edit_client 3")
        return

    param = args[1]  # Получаем параметр (например, число 3)

    if not param.isdigit():  # Проверяем, что параметр — число
        await message.reply("Ошибка! Параметр должен быть числом.")
        return

    ids = await get_ids_from_db(businessman_id)
    ids = ids[::-1]
    await message.reply(str(ids[int(param)-1]))


# async def process_edit_client(message: types.Message):
# @router.callback_query(lambda c: c.data == "next_page")
# Запуск процесса поллинга новых апдейтов
async def main():
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())