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
    Message,
    CallbackQuery
)

# --- НАСТРОЙКИ И ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1213392194"))  # Твой Telegram ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- БАЗА ДАННЫХ В ПАМЯТИ ---
# Список всех пользователей для рассылки
all_users = set()

# Доступные слоты времени
available_slots = ["10:00", "12:00", "14:00", "16:00", "18:00"]

# Активные записи: {user_id: {"service": ..., "radius": ..., "time": ..., "phone": ..., "name": ...}}
bookings = {}

# --- FSM СОСТОЯНИЯ ---
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
        [KeyboardButton(text="📅 Записаться на сервис")],
        [KeyboardButton(text="📋 Моя запись"), KeyboardButton(text="📍 Де ми знаходимось")],
        [KeyboardButton(text="💰 Услуги и цены")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ Панель админа")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- СТАРТ ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    all_users.add(message.from_user.id)
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Добро пожаловать в **Felgen Welt** (г. Одесса, ул. Дмитриевская 109).\n"
        f"Выберите нужное действие в меню ниже:",
        reply_markup=main_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )

# --- ЛОКАЦИЯ ---
@dp.message(F.text == "📍 Де ми знаходимось")
async def show_location(message: Message):
    text = (
        "📍 **Felgen Welt** — шиномонтажный центр и реставрация дисков\n\n"
        "🏠 **Адрес:** г. Одесса, ул. Дмитриевская 109\n"
        "📞 **Телефон:** +380 XX XXX XX XX\n"
        "⏰ **Режим работы:** Пн-Сб с 9:00 до 19:00\n\n"
        "📍 [Открыть на Google Картах](https://maps.google.com)"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

# --- УСЛУГИ И ЦЕНЫ ---
@dp.message(F.text == "💰 Услуги и цены")
async def show_prices(message: Message):
    text = (
        "🔧 **Наши основные услуги Felgen Welt:**\n\n"
        "• Сезонная переобувка шин\n"
        "• Порошковая покраска дисков\n"
        "• Ремонт и рихтовка дисков / сварка Argon\n"
        "• Продажа шин и дисков из Германии\n\n"
        "Выберите «📅 Записаться на сервис», чтобы рассчитать точную стоимость под ваш радиус!"
    )
    await message.answer(text)

# --- МОЯ ЗАПИСЬ ---
@dp.message(F.text == "📋 Моя запись")
async def show_my_booking(message: Message):
    user_id = message.from_user.id
    if user_id in bookings:
        b = bookings[user_id]
        text = (
            f"📋 **Ваша активная запись:**\n\n"
            f"🛠 **Услуга:** {b['service']}\n"
            f"🛞 **Радиус:** {b['radius']}\n"
            f"⏰ **Время:** {b['time']}\n"
            f"📞 **Телефон:** {b['phone']}\n\n"
            f"📍 Ждем вас по адресу: ул. Дмитриевская 109"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Перенести запись", callback_query_data="reschedule")],
            [InlineKeyboardButton(text="❌ Отменить запись", callback_query_data="cancel_booking")]
        ])
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer("У вас пока нет активных записей. Нажмите «📅 Записаться на сервис».")

# --- ПРОЦЕСС ЗАПИСИ (ФЛОУ) ---
@dp.message(F.text == "📅 Записаться на сервис")
async def start_booking(message: Message, state: FSMContext):
    user_id = message.from_user.id
    all_users.add(user_id)
    if user_id in bookings:
        await message.answer("У вас уже есть активная запись! Посмотреть или изменить её можно в разделе «📋 Моя запись».")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Переобувка шин", callback_data="srv_tire")],
        [InlineKeyboardButton(text="🎨 Порошковая покраска дисков", callback_data="srv_paint")],
        [InlineKeyboardButton(text="🔨 Ремонт / Рихтовка дисков", callback_data="srv_repair")],
        [InlineKeyboardButton(text="🇩🇪 Подбор шин/дисков из Германии", callback_data="srv_import")]
    ])
    await state.set_state(BookingState.waiting_for_service)
    await message.answer("Выберите нужную услугу:", reply_markup=kb)

@dp.callback_query(BookingState.waiting_for_service)
async def process_service(callback: CallbackQuery, state: FSMContext):
    srv_map = {
        "srv_tire": "Переобувка шин",
        "srv_paint": "Порошковая покраска",
        "srv_repair": "Ремонт/Рихтовка дисков",
        "srv_import": "Подбор шин/дисков из Германии"
    }
    srv_name = srv_map.get(callback.data, "Услуга")
    await state.update_data(selected_service=srv_name)
    await callback.answer()

    # Шаг 2: Выбор радиуса
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="R13-R15", callback_data="R13-R15"), InlineKeyboardButton(text="R16-R17", callback_data="R16-R17")],
        [InlineKeyboardButton(text="R18-R19", callback_data="R18-R19"), InlineKeyboardButton(text="R20+", callback_data="R20+")]
    ])
    await state.set_state(BookingState.waiting_for_radius)
    await callback.message.answer(f"Выбрано: **{srv_name}**.\nУкажите радиус ваших колес:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(BookingState.waiting_for_radius)
async def process_radius(callback: CallbackQuery, state: FSMContext):
    radius = callback.data
    await state.update_data(selected_radius=radius)
    await callback.answer()

    # Выбор времени из свободных слотов
    if not available_slots:
        await callback.message.answer("К сожалению, на сегодня свободных слотов нет. Попробуйте позже.")
        await state.clear()
        return

    buttons = [[InlineKeyboardButton(text=f"⏰ {slot}", callback_data=f"time_{slot}")] for slot in available_slots]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(BookingState.waiting_for_time)
    await callback.message.answer("Выберите удобное время для визита:", reply_markup=kb)

@dp.callback_query(BookingState.waiting_for_time)
async def process_time(callback: CallbackQuery, state: FSMContext):
    time_selected = callback.data.replace("time_", "")
    await state.update_data(selected_time=time_selected)
    await callback.answer()

    await state.set_state(BookingState.waiting_for_phone)
    await callback.message.answer("Остался последний шаг! Напишите ваш **номер телефона** для связи:")

@dp.message(BookingState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    time_selected = data['selected_time']

    # Сохраняем бронь
    bookings[user_id] = {
        "service": data['selected_service'],
        "radius": data['selected_radius'],
        "time": time_selected,
        "phone": message.text,
        "name": user_name
    }

    # Удаляем забронированный слот из доступных
    if time_selected in available_slots:
        available_slots.remove(time_selected)

    await state.clear()

    # Клиентское подтверждение
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Перенести запись", callback_data="reschedule")],
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_booking")]
    ])
    await message.answer(
        f"✅ **Запись успешно оформлена!**\n\n"
        f"🛠 **Услуга:** {data['selected_service']}\n"
        f"🛞 **Радиус:** {data['selected_radius']}\n"
        f"⏰ **Время:** {time_selected}\n"
        f"📍 **Адрес:** г. Одесса, ул. Дмитриевская 109\n\n"
        f"Ждем вас! Если планы изменятся, вы можете перенести или отменить запись кнопками ниже.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

    # Уведомление Админу
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🚨 **НОВАЯ ЗАПИСЬ (Felgen Welt)!**\n\n"
            f"👤 **Клиент:** {user_name} (@{message.from_user.username or 'нет'})\n"
            f"📞 **Тел:** {message.text}\n"
            f"🛠 **Услуга:** {data['selected_service']}\n"
            f"🛞 **Радиус:** {data['selected_radius']}\n"
            f"⏰ **Время:** {time_selected}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки админу: {e}")

# --- ОТМЕНА И ПЕРЕНОС ЗАПИСИ КЛИЕНТОМ ---
@dp.callback_query(F.data == "cancel_booking")
async def cancel_booking_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in bookings:
        b = bookings.pop(user_id)
        # Возвращаем слот обратно в доступные
        if b['time'] not in available_slots:
            available_slots.append(b['time'])
            available_slots.sort()

        await callback.message.edit_text("❌ **Ваша запись успешно отменена.** Забронированное время снова свободно.")
        await callback.answer("Запись отменена")

        # Уведомляем админа
        try:
            await bot.send_message(
                ADMIN_ID,
                f"ℹ️ **ОТМЕНА ЗАПИСИ!**\nКлиент {b['name']} отменил запись на {b['time']} ({b['service']}). Слот снова свободен."
            )
        except Exception:
            pass
    else:
        await callback.answer("У вас нет активных записей.", show_alert=True)

@dp.callback_query(F.data == "reschedule")
async def reschedule_booking_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id in bookings:
        b = bookings.pop(user_id)
        if b['time'] not in available_slots:
            available_slots.append(b['time'])
            available_slots.sort()

        await callback.answer("Старая запись сброшена. Выберите новое время!")
        # Запускаем флоу заново
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Переобувка шин", callback_data="srv_tire")],
            [InlineKeyboardButton(text="🎨 Порошковая покраска дисков", callback_data="srv_paint")],
            [InlineKeyboardButton(text="🔨 Ремонт / Рихтовка дисков", callback_data="srv_repair")],
            [InlineKeyboardButton(text="🇩🇪 Подбор шин/дисков из Германии", callback_data="srv_import")]
        ])
        await state.set_state(BookingState.waiting_for_service)
        await callback.message.answer("Старая запись сброшена. Выберите услугу заново:", reply_markup=kb)

# --- ПАНЕЛЬ АДМИНИСТРАТОРА ---
@dp.message(F.text == "⚙️ Панель админа")
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все активные записи", callback_data="admin_list_bookings")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ Добавить свободный слот", callback_data="admin_add_slot")]
    ])
    await message.answer("🛠 **Панель администратора Felgen Welt**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_list_bookings")
async def admin_list_bookings_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    if not bookings:
        await callback.message.answer("На данный момент активных записей нет.")
    else:
        text = "📋 **Список всех текущих записей:**\n\n"
        for uid, b in bookings.items():
            text += f"⏰ **{b['time']}** — {b['name']} ({b['phone']})\n   Услуга: {b['service']} [{b['radius']}]\n---\n"
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# --- РАССЫЛКА ---
@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminState.waiting_for_broadcast)
    await callback.message.answer("Введите текст (или отправьте фото с описанием) для рассылки всем пользователям:")
    await callback.answer()

@dp.message(AdminState.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    count = 0
    await message.answer("🚀 Запуск рассылки...")
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

    await message.answer(f"✅ Рассылка успешно завершена! Доставлено **{count}** пользователям.", parse_mode="Markdown")
    await state.clear()

# --- ДОБАВЛЕНИЕ СЛОТА ---
@dp.callback_query(F.data == "admin_add_slot")
async def admin_add_slot_handler(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminState.waiting_for_new_slot)
    await callback.message.answer("Введите новое время в формате `HH:MM` (например, `19:00`):")
    await callback.answer()

@dp.message(AdminState.waiting_for_new_slot)
async def process_add_slot(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    new_slot = message.text.strip()
    if new_slot not in available_slots:
        available_slots.append(new_slot)
        available_slots.sort()
        await message.answer(f"✅ Слот `{new_slot}` успешно добавлен!")
    else:
        await message.answer("Такой слот уже существует.")
    await state.clear()

# --- ЗАПУСК БОТА ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
