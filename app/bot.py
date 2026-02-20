import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import settings
from app.database import init_db
from app.keyboards.menus import get_main_menu_keyboard


logging.basicConfig(level=logging.INFO)


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Я бот для заявок.\n\n"
        "Выберите действие в меню ниже:"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())


@dp.message(F.text == "📞 Контакты")
async def contacts_handler(message: Message) -> None:
    await message.answer(
        "📞 Контакты:\n"
        "Телефон: +7 (900) 000-00-00\n"
        "Адрес: г. Москва\n"
        "Время работы: 9:00-21:00"
    )


@dp.message(F.text == "⭐ Отзывы")
async def reviews_handler(message: Message) -> None:
    await message.answer(
        "⭐ Отзывы:\n"
        "«Очень быстро помогли!»\n"
        "«Удобный бот, всё понятно.»"
    )


@dp.message(F.text == "📝 Оставить заявку")
async def lead_start_handler(message: Message) -> None:
    await message.answer(
        "Отлично, давайте начнем.\n"
        "Введите имя клиента:",
        reply_markup=get_main_menu_keyboard(),  # пока без FSM, позже заменишь на cancel-клавиатуру
    )


async def main() -> None:
    await init_db()  # создаёт таблицы при старте (если их нет)
    bot = Bot(token=settings.bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
