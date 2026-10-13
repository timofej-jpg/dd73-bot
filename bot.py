import os
import logging
import asyncio
from typing import Any, Awaitable, Callable, Dict
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.types import (
    Message, 
    CallbackQuery, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

# 1. ЗАЩИТА ТОКЕНА (Загрузка из внешнего файла .env)
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("ОШИБКА БЕЗОПАСНОСТИ: BOT_TOKEN не найден в переменных окружения!")

# 2. ЗАЩИТА ОТ СПАМА И DDOS (Anti-Flooding Middleware)
class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 0.8):
        self.limit = limit
        self.user_timestamps = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = asyncio.get_event_loop().time()
        
        if user_id in self.user_timestamps:
            if current_time - self.user_timestamps[user_id] < self.limit:
                # Игнорируем слишком частые запросы для защиты сервера
                return
        
        self.user_timestamps[user_id] = current_time
        return await handler(event, data)


# 3. КРАСИВЫЕ КНОПКИ И ИНТЕРФЕЙС

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное интерактивное меню"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏎️ Выбрать услугу", callback_data="services"),
                InlineKeyboardButton(text="📍 Локация", callback_data="location")
            ],
            [
                InlineKeyboardButton(text="🎁 Акции и Скидки", callback_data="promo"),
                InlineKeyboardButton(text="📞 Связаться с менеджером", callback_data="contact_request")
            ]
        ]
    )
    return keyboard

def get_services_keyboard() -> InlineKeyboardMarkup:
    """Меню услуг"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧼 Комплексная мойка / Детейлинг", callback_data="service_1")],
            [InlineKeyboardButton(text="🛡️ Защитное покрытие (Керамика)", callback_data="service_2")],
            [InlineKeyboardButton(text="🛠️ Техническое обслуживание", callback_data="service_3")],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="main_menu")]
        ]
    )
    return keyboard

def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Безопасная кнопка передачи контакта без ввода личных данных"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить контакт в 1 клик", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


# 4. ОБРАБОТЧИКИ СОБЫТИЙ (HANDLERS)

dp = Dispatcher(storage=MemoryStorage())
dp.message.middleware(RateLimitMiddleware(limit=0.7))

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "👋 **Добро пожаловать в премиум-сервис!**\n\n"
        "🔒 *Мы заботимся о вашей конфиденциальности.* Вам не нужно вводить логины, "
        "пароли или личные данные. Все действия выполняются безопасно в 1 клик.\n\n"
        "Выберите интересующий раздел в меню ниже 👇"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "main_menu")
async def process_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 **Главное меню**\n\nВыберите нужный раздел:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "services")
async def process_services(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚡ **Доступные услуги:**\n\nВыберите категорию для записи:",
        parse_mode="Markdown",
        reply_markup=get_services_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("service_"))
async def process_service_select(callback: CallbackQuery):
    await callback.message.answer(
        "✅ Вы выбрали услугу!\n\n"
        "Чтобы мы забронировали за вами время, нажмите кнопку ниже и подтвердите передачу контакта.",
        reply_markup=get_contact_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "contact_request")
async def process_contact_request(callback: CallbackQuery):
    await callback.message.answer(
        "📞 Для оперативной связи с администратором нажмите кнопку ниже:",
        reply_markup=get_contact_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "location")
async def process_location(callback: CallbackQuery):
    await callback.message.edit_text(
        "📍 **Наш адрес:** ул. Центральная, 12\n"
        "⏰ **Режим работы:** Ежедневно с 09:00 до 21:00\n\n"
        "Ждем вас!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

# 5. БЕЗОПАСНАЯ ОБРАБОТКА КОНТАКТА
@dp.message(F.contact)
async def process_contact(message: Message):
    contact = message.contact
    
    # ПРОВЕРКА: контакт принадлежит именно тому, кто отправил (Защита от подмены)
    if contact.user_id != message.from_user.id:
        await message.answer("❌ Ошибка безопасности: пожалуйста, отправьте именно ваш контакт.")
        return

    # Подтверждение пользователю
    await message.answer(
        "✨ **Заявка успешно принята!**\n\n"
        "Наш менеджер свяжется с вами в течение 5 минут. Спасибо за доверие!",
        parse_mode="Markdown"
    )

# 6. ЗАПУСК БОТА С ЗАЩИТОЙ
async def main():
    bot = Bot(token=BOT_TOKEN)
    logging.basicConfig(level=logging.INFO)
    
    # Сбрасываем все накопившиеся сообщения при выключении (Защита от дублей)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
