import os
import asyncio
import logging
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Message,
    CallbackQuery
)

# --- НАЛАШТУВАННЯ ТА ЗМІННІ ОТОЧЕННЯ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1213390234"))
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- АНТИСПАМ МІДЛВАРЬ ---
class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, limit=0.7):
        self.limit = limit
        self.user_timestamps = {}

    async def __call__(self, handler, event, data):
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id:
            now = datetime.now().timestamp()
            last_time = self.user_timestamps.get(user_id, 0)
            if now - last_time < self.limit:
                if isinstance(event, CallbackQuery):
                    await event.answer("Зачекайте секунду...", show_alert=False)
                return
            self.user_timestamps[user_id] = now
        return await handler(event, data)

dp.message.middleware(AntiSpamMiddleware())
dp.callback_query.middleware(AntiSpamMiddleware())

# --- БАЗА ДАНИХ ТА СТАНЫ ---
all_users = set()

# Слоты: "YYYY-MM-DD HH:MM" -> Dict
# status: "free" | "booked" | "blocked"
slots = {}

def init_default_slots():
    now = datetime.now()
    for i in range(7):
        day_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        for hour in range(8, 20):
            slot_key = f"{day_date} {hour:02d}:00"
            if slot_key not in slots:
                slots[slot_key] = {"status": "free", "client_name": "", "client_phone": "", "services": []}

init_default_slots()

class Booking(StatesGroup):
    category = State()
    services = State()
    date = State()
    time = State()
    phone = State()

class Admin(StatesGroup):
    broadcast = State()
    manage_slots_date = State()

# --- КЛАВІАТУРИ ---
def main_keyboard(user_id):
    kb = [
        [KeyboardButton(text="📅 Записатися на послугу")],
        [KeyboardButton(text="💳 Прайс-лист"), KeyboardButton(text="📍 Де ми знаходимось")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ Панель адміна")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ПРАЙС-ЛИСТ FELGEN WELT (ДАНІ) ---
PRICES = {
    "Порошкове фарбування": {
        "Фарбування дисків R13-R16": 3000,
        "Фарбування дисків R17-R18": 4000,
        "Фарбування дисків R19-R20": 5000,
        "Фарбування дисків R21+": 6000
    },
    "Алмазна шліфовка": {
        "Алмазна проточка R15-R17": 2500,
        "Алмазна проточка R18-R20": 3500,
        "Алмазна проточка R21+": 4500
    },
    "Ремонт та реставрація": {
        "Рихтовка / Протка диска": 500,
        "Зварювання аргоном (1 см)": 150,
        "Усунення бордюрки": 400
    },
    "Шиномонтаж": {
        "Комплексний шиномонтаж R13-R16": 600,
        "Комплексний шиномонтаж R17-R19": 800,
        "Комплексний шиномонтаж R20+": 1000,
        "Балансування коліс": 300
    }
}

# --- СТАРТ ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    all_users.add(message.from_user.id)
    await message.answer(
        f"Вітаємо, {message.from_user.first_name}! 🛞\n"
        f"Ласкаво просимо до студії реставрації дисків Felgen Welt!\n"
        f"Професійне фарбування, алмазна проточка та ремонт дисків. ✨\n\n"
        f"Оберіть потрібну дію в меню нижче:",
        reply_markup=main_keyboard(message.from_user.id)
    )

# --- ДЕ МИ ЗНАХОДИМОСЬ ---
@dp.message(F.text == "📍 Де ми знаходимось")
async def show_location(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "📍 Студія дисків Felgen Welt\n\n"
        "🏠 Адреса: м. Одеса\n"
        "📞 Телефон: +380966195519\n"
        "⏰ Графік роботи: Щодня з 8:00 до 20:00\n\n"
        "📱 Наші посилання та навігація:\n"
        "• Instagram: https://www.instagram.com/felgen_welt\n"
        "• Telegram Канал: https://t.me/felgen_welt\n"
        "• Google Maps: https://maps.app.goo.gl/2u9m2nLsm2iSv8Ra8?g_st=ic"
    )
    await message.answer(text, disable_web_page_preview=True)

# --- ПРАЙС-ЛИСТ ПЕРЕГЛЯД ---
@dp.message(F.text == "💳 Прайс-лист")
async def show_price_categories(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Порошкове фарбування", callback_data="price_Порошкове фарбування")],
        [InlineKeyboardButton(text="💎 Алмазна шліфовка", callback_data="price_Алмазна шліфовка")],
        [InlineKeyboardButton(text="👨‍🏭 Ремонт та реставрація", callback_data="price_Ремонт та реставрація")],
        [InlineKeyboardButton(text="🛞 Шиномонтаж", callback_data="price_Шиномонтаж")]
    ])
    await message.answer("Оберіть напрямок для перегляду цінового прайсу:", reply_markup=kb)

@dp.callback_query(F.data.startswith("price_"))
async def show_price_by_cat(callback: CallbackQuery):
    cat_name = callback.data.replace("price_", "")
    text = f"💳 Прайс-лист: {cat_name}\n\n"
    for s_name, price in PRICES[cat_name].items():
        text += f"• {s_name}: {price} грн\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад до категорій", callback_data="back_to_prices")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "back_to_prices")
async def back_to_prices(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Порошкове фарбування", callback_data="price_Порошкове фарбування")],
        [InlineKeyboardButton(text="💎 Алмазна шліфовка", callback_data="price_Алмазна шліфовка")],
        [InlineKeyboardButton(text="👨‍🏭 Ремонт та реставрація", callback_data="price_Ремонт та реставрація")],
        [InlineKeyboardButton(text="🛞 Шиномонтаж", callback_data="price_Шиномонтаж")]
    ])
    await callback.message.edit_text("Оберіть напрямок для перегляду цінового прайсу:", reply_markup=kb)
    await callback.answer()

# --- ПРОЦЕС ЗАПИСУ ---
@dp.message(F.text == "📅 Записатися на послугу")
async def start_booking(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Порошкове фарбування", callback_data="cat_Порошкове фарбування")],
        [InlineKeyboardButton(text="💎 Алмазна шліфовка", callback_data="cat_Алмазна шліфовка")],
        [InlineKeyboardButton(text="👨‍🏭 Ремонт та реставрація", callback_data="cat_Ремонт та реставрація")],
        [InlineKeyboardButton(text="🛞 Шиномонтаж", callback_data="cat_Шиномонтаж")]
    ])
    await message.answer("Крок 1/4: Оберіть категорію послуг:", reply_markup=kb)
    await state.set_state(Booking.category)

@dp.callback_query(Booking.category, F.data.startswith("cat_"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    cat_name = callback.data.replace("cat_", "")
    await state.update_data(category=cat_name, selected_services=[])
    
    await render_services_menu(callback.message, cat_name, [])
    await state.set_state(Booking.services)
    await callback.answer()

async def render_services_menu(message_or_query, cat_name, selected):
    buttons = []
    for s_name, price in PRICES[cat_name].items():
        check = "✅ " if s_name in selected else ""
        buttons.append([InlineKeyboardButton(
            text=f"{check}{s_name} ({price} грн)",
            callback_data=f"srv_{s_name}"
        )])
    
    if selected:
        buttons.append([InlineKeyboardButton(text="➡️ Продовжити вибір дати", callback_data="done_services")])
    
    buttons.append([InlineKeyboardButton(text="❌ Скасувати запис", callback_data="cancel_booking")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    text = f"Крок 2/4: Оберіть послуги напрямку «{cat_name}» (можна декілька):"
    if isinstance(message_or_query, Message):
        await message_or_query.edit_text(text, reply_markup=kb)
    else:
        await message_or_query.message.edit_text(text, reply_markup=kb)

@dp.callback_query(Booking.services, F.data.startswith("srv_"))
async def toggle_service(callback: CallbackQuery, state: FSMContext):
    srv_name = callback.data.replace("srv_", "")
    data = await state.get_data()
    selected = data.get("selected_services", [])
    cat_name = data.get("category")

    if srv_name in selected:
        selected.remove(srv_name)
    else:
        selected.append(srv_name)

    await state.update_data(selected_services=selected)
    await render_services_menu(callback, cat_name, selected)
    await callback.answer()

@dp.callback_query(Booking.services, F.data == "done_services")
async def done_services(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("selected_services"):
        await callback.answer("Оберіть хоча б одну послугу!", show_alert=True)
        return

    init_default_slots()
    now = datetime.now()
    dates = [(now + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    buttons = []
    for d in dates:
        dt_obj = datetime.strptime(d, "%Y-%m-%d")
        formatted = dt_obj.strftime("%d.%m (%a)")
        buttons.append([InlineKeyboardButton(text=formatted, callback_data=f"date_{d}")])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати запис", callback_data="cancel_booking")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Крок 3/4: Оберіть дату для запису:", reply_markup=kb)
    await state.set_state(Booking.date)
    await callback.answer()

@dp.callback_query(Booking.date, F.data.startswith("date_"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    chosen_date = callback.data.replace("date_", "")
    await state.update_data(date=chosen_date)

    buttons = []
    row = []
    for hour in range(9, 19):
        slot_key = f"{chosen_date} {hour:02d}:00"
        if slots.get(slot_key, {}).get("status") == "free":
            row.append(InlineKeyboardButton(text=f"{hour:02d}:00", callback_data=f"time_{hour:02d}:00"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    if not buttons:
        await callback.answer("На цей день немає вільних слотів!", show_alert=True)
        return

    buttons.append([InlineKeyboardButton(text="❌ Скасувати запис", callback_data="cancel_booking")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(f"Крок 4/4: Оберіть час на {chosen_date}:", reply_markup=kb)
    await state.set_state(Booking.time)
    await callback.answer()

@dp.callback_query(Booking.time, F.data.startswith("time_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    chosen_time = callback.data.replace("time_", "")
    await state.update_data(time=chosen_time)
    
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поділитися контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.delete()
    await callback.message.answer("Завершення: Поділіться вашим номером телефону за допомогою кнопки нижче:", reply_markup=kb)
    await state.set_state(Booking.phone)
    await callback.answer()

@dp.message(Booking.phone)
async def enter_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
        client_name = message.contact.first_name or message.from_user.first_name
    else:
        phone = message.text
        client_name = message.from_user.first_name

    data = await state.get_data()
    cat = data['category']
    selected = data['selected_services']
    chosen_date = data['date']
    chosen_time = data['time']

    slot_key = f"{chosen_date} {chosen_time}"
    
    # Бронируем слот
    slots[slot_key] = {
        "status": "booked",
        "client_name": client_name,
        "client_phone": phone,
        "services": selected
    }

    total_sum = sum(PRICES[cat][s] for s in selected)
    srv_list_str = "\n".join([f"• {s}" for s in selected])

    client_text = (
        f"✅ Ваш запис успішно підтверджено!\n\n"
        f"📍 Студія Felgen Welt\n"
        f"📅 Дата та час: {chosen_date} о {chosen_time}\n"
        f"⚙️ Категорія: {cat}\n"
        f"🛠 Послуги:\n{srv_list_str}\n"
        f"💰 Орієнтовна вартість: {total_sum} грн\n\n"
        f"Чекаємо на вас! Якщо виникнуть питання: +380966195519"
    )
    await message.answer(client_text, reply_markup=main_keyboard(message.from_user.id))

    admin_text = (
        f"🔔 НОВА ЗАПИС! (Felgen Welt)\n\n"
        f"📅 Дата/Час: {chosen_date} {chosen_time}\n"
        f"👤 Клієнт: {client_name}\n"
        f"📞 Телефон: {phone}\n"
        f"⚙️ Категорія: {cat}\n"
        f"🛠 Послуги:\n{srv_list_str}\n"
        f"💰 Сума: {total_sum} грн"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logging.error(f"Не вдалося надіслати сповіщення адміну: {e}")

    await state.clear()

@dp.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Запис скасовано.")
    await callback.message.answer("Оберіть дію в меню:", reply_markup=main_keyboard(callback.from_user.id))
    await callback.answer()

# --- ПАНЕЛЬ АДМІНА ---
@dp.message(F.text == "⚙️ Панель адміна")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Переглянути всі записи", callback_data="admin_view_bookings")],
        [InlineKeyboardButton(text="⏰ Керування слотами часу", callback_data="admin_manage_slots")],
        [InlineKeyboardButton(text="📢 Розсилка користувачам", callback_data="admin_broadcast")]
    ])
    await message.answer("⚙️ Панель адміністратора Felgen Welt:", reply_markup=kb)

@dp.callback_query(F.data == "admin_view_bookings")
async def admin_view_bookings(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    booked = {k: v for k, v in slots.items() if v["status"] == "booked"}
    if not booked:
        await callback.message.edit_text("Наразі немає активних записів.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
        ]))
        await callback.answer()
        return

    text = "📋 Активні записи Felgen Welt:\n\n"
    for slot_time, data in sorted(booked.items()):
        srvs = ", ".join(data["services"])
        text += f"⏰ {slot_time}\n👤 {data['client_name']} ({data['client_phone']})\n🛠 {srvs}\n---\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# --- КЕРУВАННЯ СЛОТАМИ ЧАСУ ---
@dp.callback_query(F.data == "admin_manage_slots")
async def admin_manage_slots(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    init_default_slots()
    now = datetime.now()
    dates = [(now + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    buttons = []
    for d in dates:
        dt_obj = datetime.strptime(d, "%Y-%m-%d")
        formatted = dt_obj.strftime("%d.%m (%a)")
        buttons.append([InlineKeyboardButton(text=formatted, callback_data=f"admdate_{d}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("⏰ Керування слотами: Оберіть дату:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("admdate_"))
async def admin_select_date_slots(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    chosen_date = callback.data.replace("admdate_", "")
    await render_admin_slots_menu(callback.message, chosen_date)
    await callback.answer()

async def render_admin_slots_menu(message, chosen_date):
    buttons = []
    row = []
    for hour in range(8, 20):
        slot_key = f"{chosen_date} {hour:02d}:00"
        st = slots.get(slot_key, {}).get("status", "free")
        
        if st == "free":
            label = f"🟢 {hour:02d}:00"
        elif st == "blocked":
            label = f"🔴 {hour:02d}:00"
        else:
            label = f"🔵 {hour:02d}:00"

        row.append(InlineKeyboardButton(text=label, callback_data=f"toggle_slot_{chosen_date}_{hour:02d}:00"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 Назад до дат", callback_data="admin_manage_slots")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    text = (
        f"⏰ Керування слотами на {chosen_date}:\n"
        f"🟢 Вільний  |  🔴 Заблокований  |  🔵 Зайнятий (Запис)\n\n"
        f"• Натисніть на 🟢, щоб заблокувати слот (🔴).\n"
        f"• Натисніть на 🔴, щоб зробити його вільним (🟢).\n"
        f"• Натисніть на 🔵, щоб переглянути деталі запису."
    )
    await message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("toggle_slot_"))
async def toggle_slot_status(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    raw = callback.data.replace("toggle_slot_", "")
    parts = raw.split("_")
    chosen_date = parts[0]
    chosen_time = parts[1]
    slot_key = f"{chosen_date} {chosen_time}"

    slot_info = slots.get(slot_key, {"status": "free"})
    current_status = slot_info.get("status", "free")

    if current_status == "free":
        slots[slot_key] = {"status": "blocked", "client_name": "", "client_phone": "", "services": []}
    elif current_status == "blocked":
        slots[slot_key] = {"status": "free", "client_name": "", "client_phone": "", "services": []}
    elif current_status == "booked":
        c_name = slot_info.get("client_name", "Невідомо")
        c_phone = slot_info.get("client_phone", "Невідомо")
        await callback.answer(f"Зайнято клієнтом: {c_name} ({c_phone})", show_alert=True)
        return

    await render_admin_slots_menu(callback.message, chosen_date)
    await callback.answer()

@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin_cb(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Переглянути всі записи", callback_data="admin_view_bookings")],
        [InlineKeyboardButton(text="⏰ Керування слотами часу", callback_data="admin_manage_slots")],
        [InlineKeyboardButton(text="📢 Розсилка користувачам", callback_data="admin_broadcast")]
    ])
    await callback.message.edit_text("⚙️ Панель адміністратора Felgen Welt:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text("Введіть текст для розсилки всім користувачам бота:")
    await state.set_state(Admin.broadcast)
    await callback.answer()

@dp.message(Admin.broadcast)
async def admin_broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    count = 0
    for uid in all_users:
        try:
            await bot.send_message(uid, message.text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await message.answer(f"✅ Розсилку завершено! Надіслано {count} користувачам.", reply_markup=main_keyboard(ADMIN_ID))
    await state.clear()

# --- HEALTH CHECK SERVER ДЛЯ RENDER ---
async def handle_ping(request):
    return web.Response(text="Felgen Welt Bot is running fine!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
