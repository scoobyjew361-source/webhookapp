from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.menus import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    first_name = message.from_user.first_name if message.from_user else "друг"
    await message.answer(
        text=(
            f"Привет, {first_name}!\n\n"
            "Я бот для заявок. Выбери действие в меню ниже."
        ),
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == "📝 Оставить заявку")
async def on_create_lead(message: Message) -> None:
    await message.answer(
        "Форма заявки будет на следующем этапе. Сейчас можно проверить, что кнопка работает."
    )


@router.message(F.text == "📞 Контакты")
async def on_contacts(message: Message) -> None:
    await message.answer("Контакты: +7 (999) 111-22-33")


@router.message(F.text == "⭐ Отзывы")
async def on_reviews(message: Message) -> None:
    await message.answer("Отзывы появятся здесь. Сейчас раздел в разработке.")
