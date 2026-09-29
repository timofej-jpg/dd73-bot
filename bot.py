import os
import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, PreCheckoutQuery
from database import init_db, get_or_register_user, activate_trial, extend_pro

ADMIN_ID = 1213392194  # Твой Telegram ID
WEBAPP_URL = "https://timofej-jpg.github.io/dd73-bot/webapp/index.html"  # Стабильная ссылка

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Авто-отчет обо всех скрытых ошибках на твои сообщения ---
@dp.errors()
async def global_error_handler(event: types.ErrorEvent):
    logging.exception(f"Exception raised: {event.exception}")
    error_text = f"⚠️ **Скрытая ошибка в FishStats!**\n\n`{str(event.exception)[:3500]}`"
    try:
        await bot.send_message(ADMIN_ID, error_text, parse_mode="Markdown")
    except Exception:
        pass

# --- Команда /start ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    user = get_or_register_user(user_id, message.from_user.username, message.from_user.first_name)
    
    is_pro = user[1]
    trial_used = user[2]
    
    keyboard_buttons = [
        [InlineKeyboardButton(text="🎣 Открыть FishStats App", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    
    if not trial_used:
        keyboard_buttons.append([InlineKeyboardButton(text="🎁 Активировать 1 день PRO бесплатно", callback_data="start_trial")])
    
    keyboard_buttons.append([InlineKeyboardButton(text="⭐ Купить PRO (500 Stars / 30 дней)", callback_data="buy_pro")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    status_text = "🟢 **PRO статус активен**" if is_pro else "🔴 **Обычная версия**"
    
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        f"Твой статус: {status_text}\n\n"
        "FishStats — твой главный помощник на рыбалке (карта спотов, барометр клёва, приливы и рекомендации).",
        reply_markup=kb,
        parse_mode="Markdown"
    )

# --- Нажатие кнопки ручного триала ---
@dp.callback_query(F.data == "start_trial")
async def process_trial(call: types.CallbackQuery):
    success = activate_trial(call.from_user.id)
    if success:
        await call.answer("🎉 Вам активирован PRO доступ на 24 часа!", show_alert=True)
        await start_cmd(call.message)
    else:
        await call.answer("❌ Вы уже использовали ваш бесплатный пробный период.", show_alert=True)

# --- Оплата подписки в Telegram Stars (500 Stars ~ 500 грн / 10$) ---
@dp.callback_query(F.data == "buy_pro")
async def send_invoice(call: types.CallbackQuery):
    prices = [LabeledPrice(label="FishStats PRO (30 дней)", amount=500)] # 500 XTR
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="Подписка FishStats PRO",
        description="Полный доступ к карте спотов, умному барометру и рекомендациям прикормок на 30 дней.",
        payload="pro_monthly_subscription",
        provider_token="",  # Пустое поле для Валюты Stars
        currency="XTR",
        prices=prices
    )

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    extend_pro(message.from_user.id, days=30)
    await message.answer("🎉 Спасибо! Ваша PRO-подписка успешно продлена на 30 дней.")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
