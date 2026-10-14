import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Токен берется из переменных окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("ОШИБКА: BOT_TOKEN не найден!")

bot = telebot.TeleBot(BOT_TOKEN)

# Главное меню
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🏎️ Выбрать услугу", callback_data="services"),
        InlineKeyboardButton("📍 Локация", callback_data="location")
    )
    keyboard.row(
        InlineKeyboardButton("🎁 Акции и Скидки", callback_data="promo"),
        InlineKeyboardButton("📞 Связаться", callback_data="contact_request")
    )
    return keyboard

# Меню услуг
def get_services_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🧼 Комплексная мойка / Детейлинг", callback_data="service_1"))
    keyboard.add(InlineKeyboardButton("🛡️ Защитное покрытие (Керамика)", callback_data="service_2"))
    keyboard.add(InlineKeyboardButton("🛠️ Техническое обслуживание", callback_data="service_3"))
    keyboard.add(InlineKeyboardButton("◀️ Назад в меню", callback_data="main_menu"))
    return keyboard

# Кнопка отправки контакта
def get_contact_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("📱 Отправить контакт в 1 клик", request_contact=True))
    return keyboard

# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Добро пожаловать в премиум-сервис!**\n\n"
        "🔒 *Мы заботимся о вашей конфиденциальности.* Без лишнего ввода данных.\n\n"
        "Выберите интересующий раздел в меню ниже 👇"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Обработка инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "main_menu":
        bot.edit_message_text(
            "🏠 **Главное меню**\n\nВыберите нужный раздел:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    elif call.data == "services":
        bot.edit_message_text(
            "⚡ **Доступные услуги:**\n\nВыберите категорию для записи:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_services_keyboard()
        )
    elif call.data.startswith("service_") or call.data == "contact_request":
        bot.send_message(
            call.message.chat.id,
            "✅ Выбрано!\n\nДля подтверждения бронирования нажмите кнопку ниже:",
            reply_markup=get_contact_keyboard()
        )
    elif call.data == "location":
        bot.edit_message_text(
            "📍 **Наш адрес:** ул. Центральная, 12\n⏰ Ежедневно с 09:00 до 21:00",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    elif call.data == "promo":
        bot.answer_callback_query(call.id, "🎁 Скидка 10% на первую запись!", show_alert=True)

# Получение контакта
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    bot.send_message(
        message.chat.id,
        "✨ **Заявка успешно принята!**\nМенеджер свяжется с вами в течение 5 минут.",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
