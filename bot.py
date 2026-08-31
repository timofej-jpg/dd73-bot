import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# —— НАСТРОЙКИ БОТА ——
# Твой токен от @BotFather
BOT_TOKEN = "8721602640:AAFDAUZpGo3_uKrcG-7KZSHePBwItgYxJ-Q"

# Твой ID в Telegram
ADMIN_ID = 1213392194

bot = telebot.TeleBot(BOT_TOKEN)

# Название твоей студии
SHOP_NAME = "DD73 Detailing"

# —— ДАННЫЕ УСЛУГ (Прайс-лист) ——
SERVICES = {
    'wash': {'name': 'Професійне миття кузова', 'price': 'від 500 грн'},
    'clean': {'name': 'Хімчистка салону', 'price': 'від 2500 грн'},
    'polish': {'name': 'Полірування кузова', 'price': 'від 4000 грн'},
    'ceramic': {'name': 'Нанесення кераміки (з гарантією)', 'price': 'від 8000 грн'},
    'antirain': {'name': 'Антидощ (лобове)', 'price': '600 грн'},
    'engine': {'name': 'Детейлінг мийка двигуна', 'price': 'від 1200 грн'}
}

user_data = {}

# —— КЛАВИАТУРЫ ——
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚗 Послуги та ціни", "📅 Записатися")
    markup.row("📍 Де ми знаходимся", "📞 Контакти")
    return markup

def services_menu():
    markup = InlineKeyboardMarkup()
    for key, item in SERVICES.items():
        btn = InlineKeyboardButton(f"{item['name']} — {item['price']}", callback_data=f"service_{key}")
        markup.add(btn)
    return markup

# —— ОБРАБОТЧИКИ КОМАНД ——
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data.pop(message.chat.id, None)
    text = (
        f"Вітаємо у студії детейлінгу *{SHOP_NAME}*! 👋\n\n"
        "Оберіть потрібный розділ у меню нижче:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "🚗 Послуги та ціни")
def show_services(message):
    text = "📋 *Наші послуги та орієнтовні ціни:*\nВыберите услугу для детальной информации или записи:"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=services_menu())

@bot.message_handler(func=lambda message: message.text == "📍 Де ми знаходимся")
def show_location(message):
    text = (
        f"🏢 *Студія детейлінгу {SHOP_NAME}*\n"
        "📍 Одеса / Фонтанка\n"
        "⏰ Працюємо за попереднім записом с 9:00 до 19:00"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📞 Контакти")
def show_contacts(message):
    text = (
        "📞 *Зв'язок з нами:*\n\n"
        "Телефон / Telegram / Viber: +380XXXXXXXXX\n"
        "Пишіть або телефонуйте з будь-яких питань!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📅 Записатися")
def start_booking(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Введіть ваше *Ім'я* та *номер телефону* для зв'язку:")
    bot.register_next_step_handler(message, process_contact)

def process_contact(message):
    user_data[message.chat.id] = {'contact': message.text}
    bot.send_message(message.chat.id, "Вкажіть марку та модель вашого авто (або напишіть 'Ні'):")
    bot.register_next_step_handler(message, process_car)

def process_car(message):
    chat_id = message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['car'] = message.text
    
    text = "Оберіть послугу, на яку хочете записатися:"
    bot.send_message(chat_id, text, reply_markup=services_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def handle_service_selection(call):
    service_key = call.data.replace('service_', '')
    service_info = SERVICES.get(service_key, {})
    service_name = service_info.get('name', 'Невідома послуга')
    
    chat_id = call.message.chat.id
    
    if chat_id in user_data and 'contact' in user_data[chat_id]:
        contact = user_data[chat_id].get('contact', 'Не вказано')
        car = user_data[chat_id].get('car', 'Не вказано')
        
        # Уведомление администратору
        admin_text = (
            f"🚀 *НОВА ЗАЯВКА НА ЗАПИС!*\n\n"
            f"👤 *Клієнт:* {contact}\n"
            f"🚗 *Авто:* {car}\n"
            f"🛠 *Послуга:* {service_name}\n"
            f"💰 *Ціна:* {service_info.get('price', '')}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")
            
        # Подтверждение клиенту
        client_text = (
            f"✅ *Дякуємо! Твою заявку прийнято.*\n\n"
            f"🛠 *Обрана послуга:* {service_name}\n"
            f"Ми зв'яжемося з тобою найближчим часом для уточнення часу!"
        )
        bot.send_message(chat_id, client_text, parse_mode="Markdown")
        user_data.pop(chat_id, None)
    else:
        text = f"Вы выбрали: *{service_name}* ({service_info.get('price', '')}).\nНажмите '📅 Записатися' в главном меню, чтобы оставить заявку!"
        bot.send_message(chat_id, text, parse_mode="Markdown")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
