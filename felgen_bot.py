import os
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# -------------------------------------------------------------
# НАСТРОЙКИ
# -------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1213392194"))

WAZE_URL = "https://waze.com/ul/hu8mb54ps6"
GOOGLE_MAPS_URL = "https://maps.app.goo.gl/pqbuyYTiRKBa9Hjo6?g_st=ic"
INSTAGRAM_URL = "https://www.instagram.com/felgen_welt?stkn=N2w0YWxlZXNjdHN0"

# База пользователей для рассылки (в продакшене лучше БД, пока в памяти)
registered_users = set()

# -------------------------------------------------------------
# СОСТОЯНИЯ (FSM)
# -------------------------------------------------------------
class BookingState(StatesGroup):
    waiting_for_service = State()
    waiting_for_radius = State()
    waiting_for_tire_option = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_contact = State()

class AdminState(StatesGroup):
    waiting_for_broadcast_text = State()

# -------------------------------------------------------------
# КЛАВИАТУРЫ
# -------------------------------------------------------------
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записатися на сервіс")],
            [KeyboardButton(text="📌 Де ми знаходимось та контакти")]
        ],
        resize_keyboard=True
    )

def get_info_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗺 Google Maps", url=GOOGLE_MAPS_URL), InlineKeyboardButton(text="🚘 Waze", url=WAZE_URL)],
            [InlineKeyboardButton(text="📸 Наш Instagram", url=INSTAGRAM_URL)]
        ]
    )

def get_contact_request_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)],
            [KeyboardButton(text="❌ Скасувати")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_services_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛞 Сезонний шиномонтаж / Перевзуття", callback_data="srv_tire")],
            [InlineKeyboardButton(text="✨ Порошкове фарбування дисків", callback_data="srv_paint")],
            [InlineKeyboardButton(text="🛠 Ремонт та вирівнювання дисків", callback_data="srv_repair")],
            [InlineKeyboardButton(text="🇩🇪 Підбір дисків/резини з Німеччини", callback_data="srv_germany")]
        ]
    )

def get_radius_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="R13-R15", callback_data="rad_R13-R15"), InlineKeyboardButton(text="R16-R17", callback_data="rad_R16-R17")],
            [InlineKeyboardButton(text="R18-R19", callback_data="rad_R18-R19"), InlineKeyboardButton(text="R20-R22+", callback_data="rad_R20-R22+")]
        ]
    )

def get_tire_option_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛞 З власною гумою", callback_data="opt_own")],
            [InlineKeyboardButton(text="📦 Купівля / Підбір у вас", callback_data="opt_buy")]
        ]
    )

def get_days_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сьогодні", callback_data="day_Сьогодні"), InlineKeyboardButton(text="Завтра", callback_data="day_Завтра")],
            [InlineKeyboardButton(text="Післязавтра", callback_data="day_Післязавтра")]
        ]
    )

def get_time_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="09:00", callback_data="time_09:00"), InlineKeyboardButton(text="11:00", callback_data="time_11:00")],
            [InlineKeyboardButton(text="13:00", callback_data="time_13:00"), InlineKeyboardButton(text="15:00", callback_data="time_15:00")],
            [InlineKeyboardButton(text="17:00", callback_data="time_17:00")]
        ]
    )

# -------------------------------------------------------------
# ХЕНДЛЕРЫ
# -------------------------------------------------------------
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    registered_users.add(message.chat.id)
    await message.answer(
        "Вітаємо у **Felgen Welt**! 🛞🇩🇪\n\n"
        "Професійний шиномонтаж, фарбування дисків та імпорт гуми з Німеччини.\n"
        "Оберіть потрібний розділ нижче:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# --- ОБЪЕДИНЕННЫЙ РАЗДЕЛ: ЛОКАЦИЯ И КОНТАКТЫ ---
@dp.message(F.text == "📌 Де ми знаходимось та контакти")
async def show_all_info(message: types.Message):
    info_text = (
        "📍 **Адреса:** м. Одеса, вул. Дмитріївська, 109\n"
        "📞 **Телефон:** +380 63 044 9999 (Viber/WhatsApp)\n\n"
        "🕒 **Графік роботи:**\n"
        "• Пн – Сб: 09:00 – 19:00\n"
        "• Нд: 10:00 – 18:00\n\n"
        "🛠 **Основні послуги:**\n"
        "• Сезонна зміна шин\n"
        "• Порошкове фарбування та полірування дисків\n"
        "• Диски та резина з Німеччини 🇩🇪\n\n"
        "Оберіть зручний спосіб навігації або перегляньте наші роботи:"
    )
    await message.answer(info_text, reply_markup=get_info_inline_keyboard(), parse_mode="Markdown")

# --- ЗАПИСЬ: Шаг 1 (Выбор услуги) ---
@dp.message(F.text == "📅 Записатися на сервіс")
async def start_booking(message: types.Message, state: FSMContext):
    await state.set_state(BookingState.waiting_for_service)
    await message.answer("Оберіть послугу:", reply_markup=get_services_inline_keyboard())

@dp.callback_query(BookingState.waiting_for_service, F.data.startswith("srv_"))
async def process_service(callback: types.CallbackQuery, state: FSMContext):
    srv_map = {
        "srv_tire": "Сезонний шиномонтаж",
        "srv_paint": "Порошкове фарбування",
        "srv_repair": "Ремонт дисків",
        "srv_germany": "Підбір дисків/резини"
    }
    selected_srv = srv_map.get(callback.data, "Сервіс")
    await state.update_data(selected_service=selected_srv)
    await callback.answer()

    # Если выбрана переобувка или ремонт — спрашиваем радиус дисков
    if callback.data in ["srv_tire", "srv_repair", "srv_paint"]:
        await state.set_state(BookingState.waiting_for_radius)
        await callback.message.answer(f"Обрано: **{selected_srv}**\n\nВкажіть радиус дисків:", reply_markup=get_radius_inline_keyboard(), parse_mode="Markdown")
    else:
        await state.set_state(BookingState.waiting_for_date)
        await callback.message.answer(f"Обрано: **{selected_srv}**\n\nОберіть день візиту:", reply_markup=get_days_inline_keyboard(), parse_mode="Markdown")

# --- ЗАПИСЬ: Шаг 2 (Выбор радиуса) ---
@dp.callback_query(BookingState.waiting_for_radius, F.data.startswith("rad_"))
async def process_radius(callback: types.CallbackQuery, state: FSMContext):
    radius = callback.data.split("_")[1]
    await state.update_data(radius=radius)
    await callback.answer()

    data = await state.get_data()
    if data.get("selected_service") == "Сезонний шиномонтаж":
        await state.set_state(BookingState.waiting_for_tire_option)
        await callback.message.answer(f"Радіус: **{radius}**\n\nУ вас своя гума чи потрібен підбір?", reply_markup=get_tire_option_inline_keyboard(), parse_mode="Markdown")
    else:
        await state.set_state(BookingState.waiting_for_date)
        await callback.message.answer(f"Радіус: **{radius}**\n\nОберіть день візиту:", reply_markup=get_days_inline_keyboard(), parse_mode="Markdown")

# --- ЗАПИСЬ: Шаг 3 (Параметры резины) ---
@dp.callback_query(BookingState.waiting_for_tire_option, F.data.startswith("opt_"))
async def process_tire_option(callback: types.CallbackQuery, state: FSMContext):
    option = "З власною гумою" if callback.data == "opt_own" else "Потрібен підбір/купівля"
    await state.update_data(tire_option=option)
    await callback.answer()

    await state.set_state(BookingState.waiting_for_date)
    await callback.message.answer(f"Опція: **{option}**\n\nОберіть день візиту:", reply_markup=get_days_inline_keyboard(), parse_mode="Markdown")

# --- ЗАПИСЬ: Шаг 4 (Выбор дня) ---
@dp.callback_query(BookingState.waiting_for_date, F.data.startswith("day_"))
async def process_day(callback: types.CallbackQuery, state: FSMContext):
    selected_day = callback.data.split("_")[1]
    await state.update_data(selected_day=selected_day)
    await callback.answer()

    await state.set_state(BookingState.waiting_for_time)
    await callback.message.answer(f"День: **{selected_day}**\n\nОберіть час:", reply_markup=get_time_inline_keyboard(), parse_mode="Markdown")

# --- ЗАПИСЬ: Шаг 5 (Выбор времени) ---
@dp.callback_query(BookingState.waiting_for_time, F.data.startswith("time_"))
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    selected_time = callback.data.split("_")[1]
    await state.update_data(selected_time=selected_time)
    await callback.answer()

    await state.set_state(BookingState.waiting_for_contact)
    data = await state.get_data()

    details = (
        f"📌 **Деталі вашої заявки:**\n"
        f"🛠 **Послуга:** {data.get('selected_service')}\n"
        f"{'📏 **Радіус:** ' + data.get('radius') + '\n' if data.get('radius') else ''}"
        f"{'🛞 **Гума:** ' + data.get('tire_option') + '\n' if data.get('tire_option') else ''}"
        f"📅 **Дата:** {data.get('selected_day')}\n"
        f"⏰ **Час:** {selected_time}\n\n"
        "Натисніть **«📱 Поділитися контактом»** нижче:"
    )
    await callback.message.answer(details, reply_markup=get_contact_request_keyboard(), parse_mode="Markdown")

# --- ЗАПИСЬ: Шаг 6 (Контакт + Уведомление админа + Напоминание) ---
@dp.message(BookingState.waiting_for_contact, F.contact)
async def process_contact(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    phone = message.contact.phone_number
    name = message.contact.first_name or message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "без username"

    await message.answer(
        "✅ **Заявку прийнято!**\n\nМы зв'яжемося з вами для підтвердження. Чекаємо у Felgen Welt!",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

    admin_text = (
        "🚨 **НОВА ЗАПИС! (Felgen Welt)**\n\n"
        f"🛠 **Послуга:** {user_data.get('selected_service')}\n"
        f"📏 **Радіус:** {user_data.get('radius', 'Не вказано')}\n"
        f"🛞 **Варіант гуми:** {user_data.get('tire_option', 'Не вказано')}\n"
        f"📅 **Коли:** {user_data.get('selected_day')}, {user_data.get('selected_time')}\n\n"
        f"👤 **Клієнт:** {name} ({username})\n"
        f"📞 **Тел:** +{phone if not phone.startswith('+') else phone}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Помилка надсилання адміну: {e}")

    await state.clear()

@dp.message(F.text == "❌ Скасувати")
async def cancel_booking(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Запис скасовано.", reply_markup=get_main_keyboard())

# -------------------------------------------------------------
# АДМИН-ПАНЕЛЬ И РАССЫЛКА
# -------------------------------------------------------------
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📢 Зробити рассылку", callback_data="admin_broadcast")]]
    )
    await message.answer(f"👑 **Панель адміністратора Felgen Welt**\n\nУ базі користувачів: {len(registered_users)}", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminState.waiting_for_broadcast_text)
    await callback.message.answer("Введіть текст рассылки для всіх клієнтів:")
    await callback.answer()

@dp.message(AdminState.waiting_for_broadcast_text)
async def execute_broadcast(message: types.Message, state: FSMContext, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    
    count = 0
    for user_id in registered_users:
        try:
            await bot.send_message(chat_id=user_id, text=message.text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await message.answer(f"✅ Рассылку успішно надіслано **{count}** користувачам!")
    await state.clear()

# -------------------------------------------------------------
# ЗАПУСК
# -------------------------------------------------------------
async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
