import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# —— НАСТРОЙКИ БОТА ——
BOT_TOKEN = "8721602640:AAG5kjtNor9RJUGfDkRSXtAUz_lsikNPxA4"
ADMIN_ID = 1213392194

bot = telebot.TeleBot(BOT_TOKEN)
SHOP_NAME = "dd73_detailing"
TG_CHANNEL = "https://t.me/dd73_detailing"

# —— ДАННЫЕ УСЛУГ ——
SERVICES = {
    'wash': {'name': '🧽 Детейлінг мийка кузова', 'price': 'від 600 грн'},
    'clean': {'name': '🧹 Глибока хімчистка салону', 'price': 'від 3000 грн'},
    'polish': {'name': '✨ Полірування кузова', 'price': 'від 4500 грн'},
    'ceramic': {'name': '🛡 Нанесення кераміки', 'price': 'від 8500 грн'},
    'ppf': {'name': '🚗 Бронеплівка (PPF)', 'price': 'від 12000 грн'},
    'antirain': {'name': '🌧 Покриття «Антидощ»', 'price': '800 грн'}
}

# Временное хранение данных пользователей
user_data = {}

# —— ГЛАВНОЕ МЕНЮ (С ПРОВЕРКОЙ НА АДМИНА) ——
def get_main_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚗 Послуги та ціни", "📅 Записатися")
    markup.row("📍 Де ми знаходимось", "📞 Контакти")
    markup.row("💬 Наш Telegram-канал / Відгуки")
    
    # Кнопка админа появится только у тебя
    if user_id == ADMIN_ID:
        markup.row("👑 Панель Адміна")
        
    return markup

# —— ИНЛАЙН-КНОПКИ ДЛЯ ВЫБОРА ДАТЫ И ВРЕМЕНИ ——
def get_days_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Сьогодні", callback_data="day_Сьогодні"),
        InlineKeyboardButton("Завтра", callback_data="day_Завтра"),
        InlineKeyboardButton("Післязавтра", callback_data="day_Післязавтра")
    )
    return markup

def get_time_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("10:00", callback_data="time_10:00"),
        InlineKeyboardButton("12:00", callback_data="time_12:00"),
        InlineKeyboardButton("14:00", callback_data="time_14:00")
    )
    markup.row(
        InlineKeyboardButton("16:00", callback_data="time_16:00"),
        InlineKeyboardButton("18:00", callback_data="time_18:00")
    )
    return markup

def services_menu():
    markup = InlineKeyboardMarkup()
    for key, item in SERVICES.items():
        btn = InlineKeyboardButton(f"{item['name']} — {item['price']}", callback_data=f"service_{key}")
        markup.add(btn)
    return markup

def channel_inline_menu():
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton("📢 Перейти у Telegram-канал", url=TG_CHANNEL)
    markup.add(btn)
    return markup

# —— ОБРАБОТЧИКИ КОМАНД ——
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data.pop(message.chat.id, None)
    text = (
        f"Вітаємо у студії детейлінгу *{SHOP_NAME}*! 🔥\n\n"
        "✨ ДЕТЕЙЛІНГ | ХІМЧИСТКА | ПОЛІРУВАННЯ | КЕРАМІКА | БРОНЕПЛІВКА ✨\n\n"
        "Оберіть потрібний розділ у меню нижче:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: message.text == "👑 Панель Адміна")
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        text = (
            "👑 *Панель Адміністратора dd73_detailing*\n\n"
            "Вы вошли как главный администратор.\n"
            "Все новые заявки клиентов от ботов приходят прямо сюда в ЛС!"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "Доступ заборонено.")

@bot.message_handler(func=lambda message: message.text == "🚗 Послуги та ціни")
def show_services(message):
    text = "📋 *Наші послуги та прайс:*\nОберіть послугу для детальної інформації або запису:"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=services_menu())

@bot.message_handler(func=lambda message: message.text == "📍 Де ми знаходимось")
def show_location(message):
    text = (
        f"🏢 *Студія детейлінгу {SHOP_NAME}*\n\n"
        "📍 *Адреса:* ул. Дюківська 3, Одеса\n"
        "⏰ *Графік роботи:* 9:00 - 20:00 (за попереднім записом)"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📞 Контакти")
def show_contacts(message):
    text = (
        f"📞 *Зв'язок з {SHOP_NAME}:*\n\n"
        "📱 *Запис по телефону:* 073 567 73 73\n"
        "📍 *Адреса:* Дюківська 3, Одеса\n\n"
        "Пишіть або телефонуйте з будь-яких питань!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💬 Наш Telegram-канал / Відгуки")
def show_channel(message):
    text = "📢 Підписуйтесь на наш офіційний канал, щоб дивитися роботи, до/після та читати відгуки:"
    bot.send_message(message.chat.id, text, reply_markup=channel_inline_menu())

# —— ПРОЦЕСС ЗАПИСИ НА КНОПКАХ ——
@bot.message_handler(func=lambda message: message.text == "📅 Записатися")
def start_booking(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Введіть ваше *Ім'я* та *номер телефону* для зв'язку:")
    bot.register_next_step_handler(message, process_contact)

def process_contact(message):
    user_data[message.chat.id]['contact'] = message.text
    bot.send_message(message.chat.id, "Вкажіть марку та модель вашого авто:")
    bot.register_next_step_handler(message, process_car)

def process_car(message):
    user_data[message.chat.id]['car'] = message.text
    bot.send_message(message.chat.id, "Оберіть зручний день для запису:", reply_markup=get_days_keyboard())

# Обработка выбора дня
@bot.callback_query_handler(func=lambda call: call.data.startswith('day_'))
def handle_day_selection(call):
    day = call.data.replace('day_', '')
    chat_id = call.message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['day'] = day
        bot.edit_message_text(f"День обрано: *{day}*\nТепер оберіть зручний час:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=get_time_keyboard())

# Обработка выбора времени
@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time_selection(call):
    time_val = call.data.replace('time_', '')
    chat_id = call.message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['time'] = time_val
        bot.edit_message_text(f"Час обрано: *{user_data[chat_id].get('day', '')} о {time_val}*\nТепер оберіть потрібну послугу:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=services_menu())

# Финальный шаг — выбор услуги и отправка заявки
@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def handle_service_selection(call):
    service_key = call.data.replace('service_', '')
    service_info = SERVICES.get(service_key, {})
    service_name = service_info.get('name', 'Невідома послуга')
    
    chat_id = call.message.chat.id
    
    if chat_id in user_data and 'contact' in user_data[chat_id]:
        contact = user_data[chat_id].get('contact', 'Не вказано')
        car = user_data[chat_id].get('car', 'Не вказано')
        day = user_data[chat_id].get('day', 'Не вказано')
        time_val = user_data[chat_id].get('time', 'Не вказано')
        
        # Заявка администратору
        admin_text = (
            f"🚀 *НОВА ЗАЯВКА НА ЗАПИС! (dd73_detailing)*\n\n"
            f"👤 *Клієнт:* {contact}\n"
            f"🚗 *Авто:* {car}\n"
            f"📅 *Дата і час:* {day} о {time_val}\n"
            f"🛠 *Послуга:* {service_name}\n"
            f"💰 *Ціна:* {service_info.get('price', '')}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Помилка відправки адміну: {e}")
            
        # Подтверждение клиенту
        client_text = (
            f"✅ *Дякуємо! Вашу заявку прийнято.*\n\n"
            f"🛠 *Послуга:* {service_name}\n"
            f"📅 *Час:* {day} о {time_val}\n\n"
            f"Ми зв'яжемося з вами найближчим часом для підтвердження!"
        )
        bot.edit_message_text(client_text, chat_id, call.message.message_id, parse_mode="Markdown")
        user_data.pop(chat_id, None)
    else:
        text = f"Ви обрали: *{service_name}* ({service_info.get('price', '')}).\nНатисніть '📅 Записатися' у головному меню, щоб оформити запис!"
        bot.send_message(chat_id, text, parse_mode="Markdown")

if __name__ == '__main__':
    bot.infinity_polling()
