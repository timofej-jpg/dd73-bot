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
# НАСТРОЙКИ (Замени на свои данные)
# -------------------------------------------------------------
BOT_TOKEN = "8721602640:AAFDAUZpGo3_uKrcG-7KZSHePBwItgYxJ-Q"
ADMIN_ID = 1213392194 # Твой Telegram ID или ID администратора студии

WAZE_URL = "https://waze.com/ul/hu8mb6vg0f"
GOOGLE_MAPS_URL = "https://maps.app.goo.gl/TJWZ8gNNJfeNVpAJ9?g_st=ic"

# -------------------------------------------------------------
# СОСТОЯНИЯ (FSM)
# -------------------------------------------------------------
class BookingState(StatesGroup):
    waiting_for_service = State()
    waiting_for_contact = State()

# -------------------------------------------------------------
# КЛАВИАТУРЫ
# -------------------------------------------------------------
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записатися на сервіс")],
            [KeyboardButton(text="📌 Де ми знаходимось"), KeyboardButton(text="📞 Контакти")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_location_inline_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗺 Відкрити в Google Maps", url=GOOGLE_MAPS_URL)],
            [InlineKeyboardButton(text="🚘 Відкрити в Waze", url=WAZE_URL)]
        ]
    )
    return keyboard

def get_contact_request_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)],
            [KeyboardButton(text="❌ Скасувати")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# Заглушка для услуг (завтра подставим реальный прайс и фото)
def get_services_inline_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧽 Хімчистка салону", callback_data="service_chem")],
            [InlineKeyboardButton(text="✨ Полірування та кераміка", callback_data="service_polish")],
            [InlineKeyboardButton(text="🧼 Комплексная мийка", callback_data="service_wash")]
        ]
    )
    return keyboard

# -------------------------------------------------------------
# ХЕНДЛЕРЫ
# -------------------------------------------------------------
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Вітаємо у **DD73 Detailing & Car Spa**! 🚘✨\n\n"
        "Оберіть потрібный розділ у меню нижче:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# --- РАЗДЕЛ: ГЕОЛОКАЦИЯ ---
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

# --- РАЗДЕЛ: КОНТАКТЫ ---
@dp.message(F.text == "📞 Контакти")
async def show_contacts(message: types.Message):
    await message.answer(
        "📞 **Зв'язок з нами:**\n"
        "Телефон: +380 XX XXX XX XX\n"
        "Графік роботи: Щодня з 09:00 до 19:00\n\n"
        "Завжди раді бачити вас!",
        parse_mode="Markdown"
    )

# --- РАЗДЕЛ: ЗАПИСЬ НА СЕРВИС ---
@dp.message(F.text == "📅 Записатися на сервіс")
async def start_booking(message: types.Message, state: FSMContext):
    await state.set_state(BookingState.waiting_for_service)
    await message.answer(
        "Оберіть послугу, яка вас цікавить:",
        reply_markup=get_services_inline_keyboard()
    )

# Выбор услуги через inline-кнопку
@dp.callback_query(BookingState.waiting_for_service, F.data.startswith("service_"))
async def process_service_selection(callback: types.CallbackQuery, state: FSMContext):
    services_map = {
        "service_chem": "Хімчистка салону",
        "service_polish": "Полірування та кераміка",
        "service_wash": "Комплексная мийка"
    }
    selected_service = services_map.get(callback.data, "Послуга")
    await state.update_data(selected_service=selected_service)
    
    await callback.answer()
    await state.set_state(BookingState.waiting_for_contact)
    
    # Запрос контакта в один клик
    await callback.message.answer(
        f"Ви обрали: **{selected_service}**.\n\n"
        "Натисніть кнопку нижче **«📱 Поділитися контактом»**, щоб ми могли підтвердити вашу заявку та узгодити час:",
        reply_markup=get_contact_request_keyboard(),
        parse_mode="Markdown"
    )

# Получение контакта (автоматически через кнопке)
@dp.message(BookingState.waiting_for_contact, F.contact)
async def process_contact(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    service = user_data.get("selected_service", "Не вказано")
    
    phone_number = message.contact.phone_number
    first_name = message.contact.first_name or message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Немає username"

    # 1. Отправляем подтверждение клиенту
    await message.answer(
        "✅ **Дякуємо! Заявку прийнято.**\n\n"
        f"🛠 **Послуга:** {service}\n"
        f"📱 **Ваш номер:** {phone_number}\n\n"
        "Наш менеджер зв'яжеться з вами найближчим часом для уточнення дати та часу!",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

    # 2. Уведомление администратору/заказчику
    admin_text = (
        "🚨 **НОВА ЗАЯВКА НА ЗАПИС!**\n\n"
        f"🛠 **Послуга:** {service}\n"
        f"👤 **Клієнт:** {first_name} ({username})\n"
        f"📞 **Телефон:** {phone_number}"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Не вдалося надіслати повідомлення адміну: {e}")

    await state.clear()

# Отмена записи
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
