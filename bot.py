import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# —— НАЛАШТУВАННЯ БОТА ——
BOT_TOKEN = "8721602640:AAG5kjtNor9RJUGfDkRSXtAUz_lsikNPxA4"
ADMIN_ID = 1213392194

bot = telebot.TeleBot(BOT_TOKEN)
SHOP_NAME = "dd73_detailing"
TG_CHANNEL = "https://t.me/dd73_detailing"

# —— ДАНІ ПОСЛУГ ——
SERVICES = {
    'wash': {'name': '🧽 Детейлінг мийка кузова', 'price': 'від 600 грн'},
    'clean': {'name': '🧹 Глибока хімчистка салону', 'price': 'від 3000 грн'},
    'polish': {'name': '✨ Полірування кузова', 'price': 'від 4500 грн'},
    'ceramic': {'name': '🛡 Нанесення кераміки', 'price': 'від 8500 грн'},
    'ppf': {'name': '🚗 Бронеплівка (PPF)', 'price': 'від 12000 грн'},
    'antirain': {'name': '🌧 Покриття «Антидощ»', 'price': '800 грн'}
}

# Доступні слоти часу (за замовчуванням вільні)
DEFAULT_TIMES = ["10:00", "12:00", "14:00", "16:00", "18:00"]
time_slots = {t: True for t in DEFAULT_TIMES}  # True = ВІЛЬНО, False = ЗАЙНЯТО

# База тимчасових даних та заявок
user_data = {}
all_orders = []

# —— КЛАВІАТУРИ ——

def get_main_menu(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚗 Послуги та ціни", "📅 Записатися")
    markup.row("📍 Де ми знаходимось", "📞 Контакти")
    markup.row("💬 Наш Telegram-канал / Відгуки")
    
    # Кнопка адміністратора відображається тільки для вас
    if str(user_id) == str(ADMIN_ID):
        markup.row("👑 Панель Адміністратора")
        
    return markup

def get_days_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Сьогодні", callback_data="day_Сьогодні"),
        InlineKeyboardButton("Завтра", callback_data="day_Завтра"),
        InlineKeyboardButton("Післязавтра", callback_data="day_Післязавтра")
    )
    return markup

def get_available_time_keyboard():
    markup = InlineKeyboardMarkup()
    buttons = []
    for t, is_free in time_slots.items():
        if is_free:
            buttons.append(InlineKeyboardButton(f"🟢 {t}", callback_data=f"time_{t}"))
    
    if not buttons:
        return None
    
    # Розміщуємо по 2-3 кнопки в рядок
    for i in range(0, len(buttons), 2):
        markup.row(*buttons[i:i+2])
        
    return markup

def get_admin_slots_keyboard():
    markup = InlineKeyboardMarkup()
    for t, is_free in time_slots.items():
        status = "🟢 Вільний (натисніть щоб заблокувати)" if is_free else "🔴 Зайнятий (натисніть щоб звільнити)"
        markup.add(InlineKeyboardButton(f"{t} — {status}", callback_data=f"toggle_slot_{t}"))
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


# —— ОБРОБНИКИ КОМАНД ТА КНОПОК МЕНЮ ——

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data.pop(message.chat.id, None)
    text = (
        f"Вітаємо у студії детейлінгу *{SHOP_NAME}*! 🔥\n\n"
        "✨ ДЕТЕЙЛІНГ | ХІМЧИСТКА | ПОЛІРУВАННЯ | КЕРАМІКА | БРОНЕПЛІВКА ✨\n\n"
        "Оберіть потрібний розділ у меню нижче:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: message.text == "👑 Панель Адміністратора")
def admin_panel(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("⚙️ Керування слотами часу", "📥 Всі записи")
        markup.row("⬅️ Повернутися в головне меню")
        
        text = (
            "👑 *Панель Адміністратора dd73_detailing*\n\n"
            "Тут ви можете керувати вільним часом для запису та переглядати нові заявки."
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "⛔ У вас немає доступу до цієї панелі.")

@bot.message_handler(func=lambda message: message.text == "⬅️ Повернутися в головне меню")
def back_to_main(message):
    bot.send_message(message.chat.id, "Ви повернулися в головне меню:", reply_markup=get_main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: message.text == "⚙️ Керування слотами часу")
def manage_slots(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        text = "⚙️ *Налаштування розкладу (натисніть на слот, щоб змінити його статус):*"
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_admin_slots_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_slot_'))
def toggle_slot(call):
    if str(call.from_user.id) == str(ADMIN_ID):
        slot = call.data.replace('toggle_slot_', '')
        if slot in time_slots:
            time_slots[slot] = not time_slots[slot]
            status_text = "вільний 🟢" if time_slots[slot] else "зайнятий 🔴"
            bot.answer_callback_query(call.id, f"Слот {slot} тепер {status_text}!")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_slots_keyboard())

@bot.message_handler(func=lambda message: message.text == "📥 Всі записи")
def show_all_orders(message):
    if str(message.from_user.id) == str(ADMIN_ID):
        if not all_orders:
            bot.send_message(message.chat.id, "📭 Наразі немає активних записів.")
            return
        
        text = "📋 *Останні записи клієнтів:*\n\n"
        for idx, order in enumerate(reversed(all_orders[-10:]), 1):
            text += (
                f"*{idx}. {order['service']}*\n"
                f"👤 Клієнт: {order['contact']}\n"
                f"🚗 Авто: {order['car']}\n"
                f"📅 Час: {order['day']} о {order['time']}\n"
                "-----------------------------------\n"
            )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🚗 Послуги та ціни")
def show_services(message):
    text = "📋 *Наші послуги та прайс:*\nОберіть послугу для детальної інформації або запису:"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=services_menu())

@bot.message_handler(func=lambda message: message.text == "📍 Де ми знаходимось")
def show_location(message):
    text = (
        f"🏢 *Студія детейлінгу {SHOP_NAME}*\n\n"
        "📍 *Адреса:* вул. Дюківська 3, Одеса\n"
        "⏰ *Графік роботи:* 9:00 - 20:00 (за попереднім записом)"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📞 Контакти")
def show_contacts(message):
    text = (
        f"📞 *Контакти {SHOP_NAME}:*\n\n"
        "❓ *З усіх питань:* 073 567 73 73\n"
        "📍 *Адреса:* вул. Дюківська 3, Одеса\n"
        "⏰ *Графік роботи:* Щодня з 9:00 до 20:00\n\n"
        "Щоб записатися на послугу, скористайтеся кнопкою *«📅 Записатися»* у меню!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💬 Наш Telegram-канал / Відгуки")
def show_channel(message):
    text = "📢 Підписуйтесь на наш офіційний канал, щоб дивитися фото робіт, результати до/після та читати відгуки:"
    bot.send_message(message.chat.id, text, reply_markup=channel_inline_menu())


# —— КРОКОВИЙ ПРОЦЕС ЗАПИСУ КЛІЄНТА ——

@bot.message_handler(func=lambda message: message.text == "📅 Записатися")
def start_booking(message):
    user_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Будь ласка, введіть ваше *Ім'я* та *номер телефону* для зв'язку:", parse_mode="Markdown")
    bot.register_next_step_handler(message, process_contact)

def process_contact(message):
    user_data[message.chat.id]['contact'] = message.text
    bot.send_message(message.chat.id, "Вкажіть марку та модель вашого автомобіля:", parse_mode="Markdown")
    bot.register_next_step_handler(message, process_car)

def process_car(message):
    user_data[message.chat.id]['car'] = message.text
    bot.send_message(message.chat.id, "Оберіть зручний день для візиту:", reply_markup=get_days_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('day_'))
def handle_day_selection(call):
    day = call.data.replace('day_', '')
    chat_id = call.message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['day'] = day
        
        time_kb = get_available_time_keyboard()
        if not time_kb:
            bot.edit_message_text("На жаль, на цей день немає вільних слотів часу. Зв'яжіться з нами за телефоном.", chat_id, call.message.message_id)
            return
            
        bot.edit_message_text(f"Обрано день: *{day}*\nТепер оберіть зручний час з доступних:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=time_kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time_selection(call):
    time_val = call.data.replace('time_', '')
    chat_id = call.message.chat.id
    if chat_id in user_data:
        user_data[chat_id]['time'] = time_val
        bot.edit_message_text(f"Обрано час: *{user_data[chat_id].get('day', '')} о {time_val}*\nТепер оберіть потрібну послугу:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=services_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def handle_service_selection(call):
    service_key = call.data.replace('service_', '')
    service_info = SERVICES.get(service_key, {})
    service_name = service_info.get('name', 'Послуга')
    
    chat_id = call.message.chat.id
    
    if chat_id in user_data and 'contact' in user_data[chat_id]:
        contact = user_data[chat_id].get('contact', 'Не вказано')
        car = user_data[chat_id].get('car', 'Не вказано')
        day = user_data[chat_id].get('day', 'Не вказано')
        time_val = user_data[chat_id].get('time', 'Не вказано')
        
        # Автоматично маркуємо обраний час як ЗАЙНЯТИЙ
        if time_val in time_slots:
            time_slots[time_val] = False
            
        # Записуємо в історію
        order_entry = {
            'contact': contact,
            'car': car,
            'day': day,
            'time': time_val,
            'service': service_name
        }
        all_orders.append(order_entry)
        
        # 1. Надсилаємо сповіщення Адміну в ЛС
        admin_text = (
            f"🚨 *НОВА ЗАЯВКА НА ЗАПИС! (dd73_detailing)*\n\n"
            f"👤 *Клієнт:* {contact}\n"
            f"🚗 *Марка та модель авто:* {car}\n"
            f"📅 *Дата та час:* {day} о {time_val}\n"
            f"🛠 *Послуга:* {service_name}\n"
            f"💰 *Орієнтовна вартість:* {service_info.get('price', '')}"
        )
        try:
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Помилка відправки адміну: {e}")
            
        # 2. Підтвердження для клієнта
        client_text = (
            f"✅ *Дякуємо за запис! Ми чекаємо на вас!*\n\n"
            f"🛠 *Послуга:* {service_name}\n"
            f"📅 *Час візиту:* {day} о {time_val}\n"
            f"📍 *Адреса:* вул. Дюківська 3, Одеса\n\n"
            f"Наш менеджер зв'яжеться з вами найближчим часом для підтвердження!"
        )
        bot.edit_message_text(client_text, chat_id, call.message.message_id, parse_mode="Markdown")
        user_data.pop(chat_id, None)
    else:
        text = f"Ви обрали: *{service_name}* ({service_info.get('price', '')}).\nНатисніть '📅 Записатися' у головному меню, щоб оформити запис!"
        bot.send_message(chat_id, text, parse_mode="Markdown")

if __name__ == '__main__':
    print("Бот dd73_detailing успішно запущений...")
    bot.infinity_polling()
