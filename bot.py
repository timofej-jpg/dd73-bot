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

user_data = {}

# —— МЕНЮ И КЛАВИАТУРЫ ——
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚗 Послуги та ціни", "📅 Записатися")
    markup.row("📍 Де ми знаходимось", "📞 Контакти")
    markup.row("💬 Наш Telegram-канал / Відгуки")
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
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "🚗 Послуги та ціни")
def show_services(message):
    text = "📋 *Наші послуги та прайс:*\nОберіть послугу для детальної інформації або запису:"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=services_menu())

@bot.message_handler(func=lambda message: message.text == "📍 Де ми знаходимось")
def show_location(message):
    text = (
        f"🏢 *Студія детейлінгу {SHOP_NAME}*\n\n"
        "📍 *Адреса:* ул. Дюківська 3, Одеса 📍\n"
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

# —— ПРОЦЕСС ЗАПИСИ НА УСЛУГУ ——
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
    bot.send_message(message.chat.id, "На яку *дату та час* вам зручно записатися? (наприклад: Завтра о 14:00):")
    bot.register_next_step_handler(message, process_datetime)

def process_datetime(message):
    user_data[message.chat.id]['datetime'] = message.text
    bot.send_message(message.chat.id, "Оберіть послугу, на яку хочете записатися:", reply_markup=services_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def handle_service_selection(call):
    service_key = call.data.replace('service_', '')
    service_info = SERVICES.get(service_key, {})
    service_name = service_info.get('name', 'Невідома послуга')
    
    chat_id = call.message.chat.id
    
    if chat_id in user_data and 'contact' in user_data[chat_id]:
        contact = user_data[chat_id].get('contact', 'Не вказано')
        car = user_data[chat_id].get('car', 'Не вказано')
        dt = user_data[chat_id].get('datetime', 'Не вказано')
        
        # Отправка заявки администратору в ЛС
        admin_text = (
            f"🚀 *НОВА ЗАЯВКА НА ЗАПИС! (dd73_detailing)*\n\n"
            f"👤 *Клієнт:* {contact}\n"
            f"🚗 *Авто:* {car}\n"
            f"📅 *Бажаний час:* {dt}\n"
            f"🛠 *Послуга:* {service_name}\n"
            f"💰 *Ціна:* {service_info.get('price', '')}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")
            
        # Ответ клиенту
        client_text = (
            f"✅ *Дякуємо! Вашу заявку прийнято.*\n\n"
            f"🛠 *Послуга:* {service_name}\n"
            f"📅 *Запит на час:* {dt}\n\n"
            f"Ми зв'яжемося з вами найближчим часом для підтвердження!"
        )
        bot.send_message(chat_id, client_text, parse_mode="Markdown")
        user_data.pop(chat_id, None)
    else:
        text = f"Ви обрали: *{service_name}* ({service_info.get('price', '')}).\nНатисніть '📅 Записатися' у головному меню, щоб оформити запис!"
        bot.send_message(chat_id, text, parse_mode="Markdown")

if __name__ == '__main__':
    print("Бот dd73_detailing запущен...")
    bot.infinity_polling()
