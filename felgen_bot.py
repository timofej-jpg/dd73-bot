import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Message,
    CallbackQuery
)

# --- НАЛАШТУВАННЯ ТА ЗМІННІ ОТОЧЕННЯ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1213392194"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- БАЗА ДАНИХ У ПАМ'ЯТІ ---
all_users = set()
available_slots = ["10:00", "12:00", "14:00", "16:00", "18:00"]
bookings = {}

# --- FSM СТАНИ ---
class BookingState(StatesGroup):
    waiting_for_service = State()
    waiting_for_radius = State()
    waiting_for_time = State()
    waiting_for_phone = State()

class AdminState(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_new_slot = State()

# --- МЕНЮ КНОПОК ---
def main_keyboard(user_id):
    kb = [
        [KeyboardButton(text="📅 Записатися на сервіс")],
        [KeyboardButton(text="📋 Моє бронювання"), KeyboardButton(text="📍 Де ми знаходимось")],
        [KeyboardButton(text="💰 Послуги та ціни")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ Панель адміна")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- СТАРТ ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    all_users.add(message.from_user.id)
    await message.answer(
        f"Вітаємо, {message.from_user.first_name}! 👋\n\n"
        f"Ласкаво просимо до **Felgen Welt** — професійного сервісу з обслуговування та реставрації дисків у м. Одеса.\n\n"
        f"Оберіть потрібний розділ у меню нижче:",
        reply_markup=main_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )

# --- ДЕ МИ ЗНАХОДИМОСЬ ---
@dp.message(F.text == "📍 Де ми знаходимось")
async def show_location(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "📍 **Felgen Welt** — шиномонтаж та реставрація дисків\n\n"
        "🏠 **Адреса:** м. Одеса, вул. Дмитрівська 109\n"
        "⏰ **Графік роботи:** Пн-Сб з 9:00 до 19:00\n\n"
        "📱 **Наші соціальні мережі та навігація:**\n"
        "• [📸 Instagram](https://instagram.com)\n"
        "• [🗺 Google Maps](https://maps.google.com)\n"
        "• [🚗 Waze Навігатор](https://waze.com)"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

# --- ПОСЛУГИ ТА ЦІНИ ---
@dp.message(F.text == "💰 Послуги та ціни")
async def show_prices(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "🔧 **Орієнтовні ціни на послуги Felgen Welt:**\n\n"
        "🛞 **Переобувка комплекту:**\n"
        "• R13 - R15 — від 600 грн\n"
        "• R16 - R17 — від 800 грн\n"
        "• R18 - R19 — від 1000 грн\n"
        "• R20+ — від 1300 грн\n\n"
        "🎨 **Порошкове фарбування (комплект):**\n"
        "• R13 - R16 — від 3500 грн\n"
        "• R17 - R19 — від 4500 грн\n"
        "• R20+ — від 6000 грн\n\n"
        "🔨 **Рихтовка / Зварювання аргоном:** від 400 грн/диск\n"
        "🇩🇪 **Прямі поставки шин/дисків з Німеччини:** індивідуальний розрахунок\n\n"
        "Для точності оберіть «📅 Записатися на сервіс»!"
    )
    await message.answer(text, parse_mode="Markdown")

# --- МОЄ БРОНЮВАННЯ ---
@dp.message(F.text == "📋 Моє бронювання")
async def show_my_booking(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id in bookings:
        b = bookings[user_id]
        text = (
            f"📋 **Ваше активне бронювання:**\n\n"
            f"🛠 **Послуга:** {b['service']}\n"
            f"🛞 **Радіус:** {b['radius']}\n"
            f"⏰ **Час:** {b['time']}\n"
            f"📞 **Телефон:** {b['phone']}\n\n"
            f"📍 Чекаємо на вас: вул. Дмитрівська 109"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Перенести запис", callback_data="reschedule")],
            [InlineKeyboardButton(text="❌ Скасувати запис", callback_data="cancel_booking")]
        ])
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer("У вас немає активних записів. Натисніть «📅 Записатися на сервіс».")

# --- ПРОЦЕС ЗАПИСУ ---
@dp.message(F.text == "📅 Записатися на сервіс")
async def start_booking(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    all_users.add(user_id)

    # Захист від спаму записів
    if user_id in bookings:
        await message.answer("У вас вже є активний запис! Ви можете переглянути або змінити його у розділі «📋 Моє бронювання».")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сезонна переобувка", callback_data="srv_tire")],
        [InlineKeyboardButton(text="🎨 Порошкове фарбування", callback_data="srv_paint")],
        [InlineKeyboardButton(text="🔨 Ремонт / Рихтовка дисків", callback_data="srv_repair")],
        [InlineKeyboardButton(text="🇩🇪 Підбір шин/дисків з Німеччини", callback_data="srv_import")]
    ])
    await state.set_state(BookingState.waiting_for_service)
    await message.answer("Оберіть необхідну послугу:", reply_markup=kb)

@dp.callback_query(BookingState.waiting_for_service)
async def process_service(callback: CallbackQuery, state: FSMContext):
    srv_map = {
        "srv_tire": "Сезонна переобувка",
        "srv_paint": "Порошкове фарбування",
        "srv_repair": "Ремонт/Рихтовка дисків",
        "srv_import": "Підбір з Німеччини"
    }
    srv_name = srv_map.get(callback.data, "Послуга")
    await state.update_data(selected_service=srv_name)
    await callback.answer()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="R13-R15", callback_data="R13-R15"), InlineKeyboardButton(text="R16-R17", callback_data="R16-R17")],
        [InlineKeyboardButton(text="R18-R19", callback_data="R18-R19"), InlineKeyboardButton(text="R20+", callback_data="R20+")]
    ])
    await state.set_state(BookingState.waiting_for_radius)
    await callback.message.answer(f"Обрано: **{srv_name}**.\nВкажіть радіус ваших коліс:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(BookingState.waiting_for_radius)
async def process_radius(callback: CallbackQuery, state: FSMContext):
    radius = callback.data
    await state.update_data(selected_radius=radius)
    await callback.answer()

    if not available_slots:
        await callback.message.answer("На жаль, вільних слотів немає. Спробуйте пізніше або зверніться до адміністратора.")
        await state.clear()
        return

    buttons = [[InlineKeyboardButton(text=f"⏰ {slot}", callback_data=f"time_{slot}")] for slot in available_slots]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(BookingState.waiting_for_time)
    await callback.message.answer("Оберіть зручний час для візиту:", reply_markup=kb)

@dp.callback_query(BookingState.waiting_for_time)
async def process_time(callback: CallbackQuery, state: FSMContext):
    time_selected = callback.data.replace("time_", "")
    await state.update_data(selected_time=time_selected)
    await callback.answer()

    contact_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поділитися контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(BookingState.waiting_for_phone)
    await callback.message.answer("Натисніть кнопку нижче, щоб передати ваш номер телефону для підтвердження:", reply_markup=contact_kb)

@dp.message(BookingState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    time_selected = data['selected_time']

    bookings[user_id] = {
        "service": data['selected_service'],
        "radius": data['selected_radius'],
        "time": time_selected,
        "phone": phone,
        "name": user_name
    }

    if time_selected in available_slots:
        available_slots.remove(time_selected)

    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Перенести запис", callback_data="reschedule")],
        [InlineKeyboardButton(text="❌ Скасувати запис", callback_data="cancel_booking")]
    ])
    
    await message.answer("Дякуємо! Номер отримано.", reply_markup=main_keyboard(user_id))
    await message.answer(
        f"✅ **Запис успішно оформлено!**\n\n"
        f"🛠 **Послуга:** {data['selected_service']}\n"
        f"🛞 **Радіус:** {data['selected_radius']}\n"
        f"⏰ **Час:** {time_selected}\n"
        f"📍 **Адреса:** м. Одеса, вул. Дмитрівська 109\n\n"
        f"Чекаємо на вас! Якщо плани зміняться, скористайтесь кнопками нижче.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            f"🚨 **НОВИЙ ЗАПИС (Felgen Welt)!**\n\n"
            f"👤 **Клієнт:** {user_name} (@{message.from_user.username or 'немає'})\n"
            f"📞 **Тел:** {phone}\n"
            f"🛠 **Послуга:** {data['selected_service']}\n"
            f"🛞 **Радіус:** {data['selected_radius']}\n"
            f"⏰ **Час:** {time_selected}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Помилка сповіщення адміна: {e}")

# --- СКАСУВАННЯ ТА ПЕРЕНОС ---
@dp.callback_query(F.data == "cancel_booking")
async def cancel_booking_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in bookings:
        b = bookings.pop(user_id)
        if b['time'] not in available_slots:
            available_slots.append(b['time'])
            available_slots.sort()

        await callback.message.edit_text("❌ **Ваш запис успішно скасовано.** Час знову вільний для бронювання.")
        await callback.answer("Запис скасовано")

        try:
            await bot.send_message(
                ADMIN_ID,
                f"ℹ️ **СКАСУВАННЯ ЗАПИСУ!**\nКлієнт {b['name']} скасував запис на {b['time']} ({b['service']}). Слот знову вільний."
            )
        except Exception:
            pass
    else:
        await callback.answer("У вас немає активних записів.", show_alert=True)

@dp.callback_query(F.data == "reschedule")
async def reschedule_booking_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id in bookings:
        b = bookings.pop(user_id)
        if b['time'] not in available_slots:
            available_slots.append(b['time'])
            available_slots.sort()

        await callback.answer("Старий запис скинуто. Оберіть новий час!")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сезонна переобувка", callback_data="srv_tire")],
            [InlineKeyboardButton(text="🎨 Порошкове фарбування", callback_data="srv_paint")],
            [InlineKeyboardButton(text="🔨 Ремонт / Рихтовка дисків", callback_data="srv_repair")],
            [InlineKeyboardButton(text="🇩🇪 Підбір шин/дисків з Німеччини", callback_data="srv_import")]
        ])
        await state.set_state(BookingState.waiting_for_service)
        await callback.message.answer("Старий запис скинуто. Оберіть послугу заново:", reply_markup=kb)

# --- ПАНЕЛЬ АДМІНІСТРАТОРА ---
@dp.message(F.text == "⚙️ Панель адміна")
@dp.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    if message.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Усі активні записи", callback_data="admin_list_bookings")],
        [InlineKeyboardButton(text="📢 Зробити розсилку", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ Додати вільний слот", callback_data="admin_add_slot")]
    ])
    await message.answer("🛠 **Панель адміністратора Felgen Welt**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_list_bookings")
async def admin_list_bookings_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.from_user.id != ADMIN_ID:
        return

    if not bookings:
        await callback.message.answer("На даний момент активних записів немає.")
    else:
        text = "📋 **Список усіх поточних записів:**\n\n"
        for uid, b in bookings.items():
            text += f"⏰ **{b['time']}** — {b['name']} ({b['phone']})\n   Послуга: {b['service']} [{b['radius']}]\n---\n"
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# --- РОЗСИЛКА ---
@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminState.waiting_for_broadcast)
    await callback.message.answer("Введіть текст (або надішліть фото з описом) для розсилки усім користувачам:")
    await callback.answer()

@dp.message(AdminState.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    count = 0
    await message.answer("🚀 Запуск розсилки...")
    for uid in list(all_users):
        try:
            if message.photo:
                await bot.send_photo(uid, photo=message.photo[-1].file_id, caption=message.caption)
            else:
                await bot.send_message(uid, message.text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await message.answer(f"✅ Розсилку успішно завершено! Доставлено **{count}** користувачам.", parse_mode="Markdown")
    await state.clear()

# --- ДОДАВАННЯ СЛОТА ---
@dp.callback_query(F.data == "admin_add_slot")
async def admin_add_slot_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminState.waiting_for_new_slot)
    await callback.message.answer("Введіть новий час у форматі `HH:MM` (наприклад, `19:00`):")
    await callback.answer()

@dp.message(AdminState.waiting_for_new_slot)
async def process_add_slot(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    new_slot = message.text.strip()
    if new_slot not in available_slots:
        available_slots.append(new_slot)
        available_slots.sort()
        await message.answer(f"✅ Слот `{new_slot}` успішно додано!")
    else:
        await message.answer("Такий слот вже існує.")
    await state.clear()

# --- ЗАПУСК БОТА ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
