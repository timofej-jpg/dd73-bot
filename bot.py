import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import asyncio

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
# Новая ссылка с учетом переименования репозитория:
WEBAPP_URL = "https://timofej-jpg.github.io/FishStats/webapp/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐟 Открыть FishStats", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(
        "Привет! Добро пожаловать в FishStats 🎣\n"
        "Нажми на кнопку ниже, чтобы записать улов или посмотреть статистику:",
        reply_markup=keyboard
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
