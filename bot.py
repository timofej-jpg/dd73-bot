import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardMarkup, InlineKeyboardButton

# ——— НАСТРОЙКИ БОТА ———
# Вставь сюда свой токен (HTTP API), который дал @BotFather
BOT_TOKEN = "8721602640:AAFDAUZpGo3_uKrcG-7KZSHePBwItgYxJ-Q
"

# Твой ID в Telegram (чтобы получать уведомления о заявках)
ADMIN_ID = 1213392194

bot = telebot.TeleBot(BOT_TOKEN)

# Название твоей студии
SHOP_NAME = "DD73 Detailing"

# ——— ДАННЫЕ УСЛУГ (Прайс-лист) ———
# Убраны спецсимволы, чтобы бот не выдавал ошибку Markdown
SERVICES = {
    'wash': {'name': 'Професійне миття кузова', 'price': 'від 500 грн'},
    'clean': {'name': 'Хімчистка салону', 'price': 'від 2500 грн'},
    'polish': {'name': 'Полірування кузова', 'price': 'від 4000 грн'},
    'ceramic': {'name': 'Керамічне покриття', 'price': 'від 8000 грн'},
    'engine': {'name': 'Миття двигуна (з гарантією)', 'price': 'від 1200 грн'},
    'anti_rain': {'name': 'Антидощ (лобове)', 'price': '600 грн'},
}

# Временное хранилище заявок (пока бот запущен)
user_requests = {}

# ——— КЛАВИАТУРЫ (Меню) ———

# Главное меню
def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_price = "💰 Послуги та ціни"
    btn_record = "📅 Записатися"
    btn_loc = "📍 Де ми знаємось?"
    btn_inst = "📸 Instagram"
    markup.add(btn_price, btn_record, btn_loc, btn_inst)
    return markup

# Инлайн-кнопки для выбора услуги при записи
def get_services_inline():
    markup = KeyboardMarkup(row_width=1)
    # Создаем кнопки по очереди
    for key, service in SERVICES.items():
        # В callback_data зашиваем 'book_' + ключ услуги (например, 'book_wash')
        btn = InlineKeyboardButton(text=service['name'], callback_data=f"book_{key}")
        markup.add(btn)
    return markup

# ——— ОБРАБОТЧИКИ (Команды и текст) ———

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        f"Вітаємо у {SHOP_NAME}!\n\n"
        "Ваше авто заслуговує на найкращий догляд. Оберіть пункт меню:"
    )
    # Отправляем фото (если есть ссылка, или просто текст)
    try:
        # Можешь вставить прямую ссылку на фото авто в кавычки ниже
        # bot.send_photo(message.chat.id, "ССЫЛКА_НА_ФОТО", caption=welcome_text, reply_markup=get_main_keyboard())
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())

# --- ИСПРАВЛЕННЫЙ ПРАЙС-ЛИСТ (Без Markdown) ---
@bot.message_handler(func=lambda message: message.text == "💰 Послуги та ціни")
def send_prices(message):
    # Создаем простой текст прайса без звездочек и форматирования
    text = f"💳 ПРАЙС-ЛИСТ {SHOP_NAME}:\n\n"
    
    # Перебираем услуги и добавляем их простым текстом
    for key, service in SERVICES.items():
        text += f"• {service['name']} — {service['price']}\n"
    
    text += "\n* Точна вартість залежить від класу та стану автомобіля."
    
    # Отправляем БЕЗ parse_mode, чтобы Markdown не ломал бота
    bot.send_message(message.chat.id, text)

# Локация
@bot.message_handler(func=lambda message: message.text == "📍 Де ми знаємось?")
def send_location(message):
    text = (
        f"{SHOP_NAME}\n\n"
        "📍 Адреса: [ВСТАВ СВОЮ АДРЕСУ ТУТ]\n\n"
        "Працюємо: Пн-Сб, 09:00 - 19:00\n\n"
        "Чекаємо на Вас!"
    )
    bot.send_message(message.chat.id, text)

# Instagram
@bot.message_handler(func=lambda message: message.text == "📸 Instagram")
def send_instagram(message):
    bot.send_message(message.chat.id, "Наш Instagram: https://instagram.com/dd73_detailing")

# ——— БЛОК ЗАПИСИ (FSM) ———

# Шаг 1: Нажатие кнопки "Записатися" -> Показываем инлайн-услуги
@bot.message_handler(func=lambda message: message.text == "📅 Записатися")
def start_booking(message):
    user_requests[message.chat.id] = {}  # Создаем пустую заявку
    text = "Оберіть послугу, на яку бажаєте записатися:"
    bot.send_message(message.chat.id, text, reply_markup=get_services_inline())

# Шаг 2: Обработка выбора услуги (Inline-кнопки)
@bot.callback_query_handler(func=lambda call: call.data.startswith('book_'))
def callback_service(call):
    # Убираем 'book_' из call.data, получаем ключ ('wash', 'clean' и т.д.)
    service_key = call.data.replace('book_', '')
    
    if service_key in SERVICES:
        # Сохраняем имя услуги в заявку
        user_requests[call.message.chat.id]['service'] = SERVICES[service_key]['name']
        
        # Убираем инлайн-кнопки
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        
        # Просим телефон
        msg = bot.send_message(call.message.chat.id, "Введіть, будь ласка, Ваш номер телефону (або залиште Ваш нікнейм у Telegram):")
        bot.register_next_step_handler(msg, process_phone)
    else:
        bot.answer_callback_query(call.id, "Помилка. Спробуйте ще раз.")

# Шаг 3: Получение телефона и завершение заявки
def process_phone(message):
    chat_id = message.chat.id
    phone_or_nick = message.text
    
    if chat_id not in user_requests or 'service' not in user_requests[chat_id]:
        bot.send_message(chat_id, "Сталася помилка. Розпочніть запис спочатку.", reply_markup=get_main_keyboard())
        return

    # Сохраняем контакт
    service_name = user_requests[chat_id]['service']
    
    # 1. Ответ пользователю
    bot.send_message(
        chat_id, 
        f"Дякуємо! Вашу заявку на '{service_name}' прийнято.\n\nМенеджер зв'яжеться з Вами найближчим часом для уточнення деталей.", 
        reply_markup=get_main_keyboard()
    )
    
    # 2. Уведомление АДМИНУ (в твой личный Telegram)
    admin_text = (
        f"🚨 НОВА ЗАЯВКА!\n\n"
        f"👤 Клієнт: {message.from_user.first_name} (@{message.from_user.username})\n"
        f"🔧 Услуга: {service_name}\n"
        f"📞 Контакт: {phone_or_nick}"
    )
    try:
        bot.send_message(ADMIN_ID, admin_text)
    except:
        print("Помилка відправки повідомлення адміну. Перевір ADMIN_ID.")
        
    # Очищаем временную заявку
    del user_requests[chat_id]

# ——— ЗАПУСК ———
if __name__ == '__main__':
    print(f"Бот {SHOP_NAME} успешно запущен на телефоне!")
    # Бот будет постоянно опрашивать сервера Telegram на наличие новых сообщений
    bot.infinity_polling()
