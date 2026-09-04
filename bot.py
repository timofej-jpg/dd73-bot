import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
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
ADMIN_ID = 1213392194


WAZE_URL = "https://waze.com/ul/hu8mb6vg0f"
GOOGLE_MAPS_URL = "https://maps.app.goo.gl/TJWZ8gNNJfeNVpAJ9?g_st=ic"

# -------------------------------------------------------------
# СОСТОЯНИЯ (FSM)
# -------------------------------------------------------------
class BookingState(StatesGroup):
    waiting_for_service = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_contact = State()

# -------------------------------------------------------------
# КЛАВИАТУРЫ
# -------------------------------------------------------------
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записатися на сервіс")],
            [KeyboardButton(text="📌 Де ми знаходимось"), KeyboardButton(text="📞 Контакти")]
        ],
        resize_keyboard=True
    )

def get_location_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗺 Відкрити в Google Maps", url=GOOGLE_MAPS_URL)],
            [InlineKeyboardButton(text="🚘 Відкрити в Waze", url=WAZE_URL)]
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
            [InlineKeyboardButton(text="🧽 Хімчистка салону", callback_data="service_chem")],
            [InlineKeyboardButton(text="✨ Полірування та кераміка", callback_data="service_polish")],
            [InlineKeyboardButton(text="🧼 Комплексна мийка", callback_data="service_wash")]
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
            [InlineKeyboardButton(text="10:00", callback_data="time_10:00"), InlineKeyboardButton(text="12:00", callback_data="time_12:00")],
            [InlineKeyboardButton(text="14:00", callback_data="time_14:00"), InlineKeyboardButton(text="16:00", callback_data="time_16:00")],
            [InlineKeyboardButton(text="18:00", callback_data="time_18:00")]
        ]
    )

# -------------------------------------------------------------
# ХЕНДЛЕРЫ
# -------------------------------------------------------------
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Вітаємо у **DD73 Detailing & Car Spa**! 🚘✨\n\n"
        "Оберіть потрібний розділ у меню нижче:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "📌 Де ми знаходимось")
async def show_location(message: types.Message):
    await message.answer(
        "📍 **Наша адреса:**\n"
        "м. Одеса, вул. Дюківська, 3\n"
        "**DD73 Detailing & Car Spa**\n\n"
        "Оберіть зручний навігатор для побудови маршруту:",
        reply_markup=get_location_inline_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "📞 Контакти")
async def show_contacts(message: types.Message):
    await message.answer(
        "📞 **Зв'язок з нами:**\n"
        "Графік роботи: Щодня з 09:00 до 19:00\n\n"
        "Чекаємо на вас!",
        parse_mode="Markdown"
    )

@dp.message(F.text == "📅 Записатися на сервіс")
async def start_booking(message: types.Message, state: FSMContext):
    await state.set_state(BookingState.waiting_for_service)
    await message.answer(
        "Оберіть послугу, яка вас цікавить:",
        reply_markup=get_services_inline_keyboard()
    )

@dp.callback_query(BookingState.waiting_for_service, F.data.startswith("service_"))
async def process_service(callback: types.CallbackQuery, state: FSMContext):
    services_map = {
        "service_chem": "Хімчистка салону",
        "service_polish": "Полірування та кераміка",
        "service_wash": "Комплексна мийка"
    }
    selected_service = services_map.get(callback.data, "Послуга")
    await state.update_data(selected_service=selected_service)
    
    await callback.answer()
    await state.set_state(BookingState.waiting_for_date)
    await callback.message.answer(
        f"Ви обрали: **{selected_service}**\n\nОберіть день візиту:",
        reply_markup=get_days_inline_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(BookingState.waiting_for_date, F.data.startswith("day_"))
async def process_day(callback: types.CallbackQuery, state: FSMContext):
    selected_day = callback.data.split("_")[1]
    await state.update_data(selected_day=selected_day)
    
    await callback.answer()
    await state.set_state(BookingState.waiting_for_time)
    await callback.message.answer(
        f"День: **{selected_day}**\n\nОберіть зручний час:",
        reply_markup=get_time_inline_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(BookingState.waiting_for_time, F.data.startswith("time_"))
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    selected_time = callback.data.split("_")[1]
    await state.update_data(selected_time=selected_time)
    
    await callback.answer()
    await state.set_state(BookingState.waiting_for_contact)
    
    data = await state.get_data()
    await callback.message.answer(
        f"📌 **Деталі запису:**\n"
        f"🛠 Послуга: {data['selected_service']}\n"
        f"📅 День: {data['selected_day']}\n"
        f"⏰ Час: {selected_time}\n\n"
        "Натисніть кнопку нижче **«📱 Поділитися контактом»**, щоб підтвердити запис:",
        reply_markup=get_contact_request_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(BookingState.waiting_for_contact, F.contact)
async def process_contact(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    
    phone_number = message.contact.phone_number
    first_name = message.contact.first_name or message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Немає username"

    await message.answer(
        "✅ **Дякуємо! Заявку прийнято.**\n\n"
        f"🛠 **Послуга:** {user_data.get('selected_service')}\n"
        f"📅 **Дата/Час:** {user_data.get('selected_day')}, {user_data.get('selected_time')}\n"
        f"📱 **Ваш номер:** {phone_number}\n\n"
        "Наш менеджер зв'яжеться з вами для підтвердження!",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

    admin_text = (
        "🚨 **НОВА ЗАЯВКА НА ЗАПИС!**\n\n"
        f"🛠 **Послуга:** {user_data.get('selected_service')}\n"
        f"📅 **День:** {user_data.get('selected_day')}\n"
        f"⏰ **Час:** {user_data.get('selected_time')}\n"
        f"👤 **Клієнт:** {first_name} ({username})\n"
        f"📞 **Телефон:** +{phone_number if not phone_number.startswith('+') else phone_number}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Помилка відправки адміну: {e}")

    await state.clear()

@dp.message(F.text == "❌ Скасувати")
async def cancel_booking(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Запис скасовано.", reply_markup=get_main_keyboard())

# -------------------------------------------------------------
# ЗАПУСК
# -------------------------------------------------------------
async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
