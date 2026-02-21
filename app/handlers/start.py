from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select

from app.content import (
    ASK_NAME_TEXT,
    BTN_CANCEL,
    BTN_CONTACTS,
    BTN_CREATE_LEAD,
    BTN_REVIEWS,
    CANCEL_TEXT,
    CONTACTS_TEXT,
    REVIEWS_TEXT,
)
from app.database import AsyncSessionLocal
from app.keyboards.menus import get_cancel_keyboard, get_main_menu_keyboard
from app.models.user import User

router = Router()


class LeadForm(StatesGroup):
    waiting_for_name = State()


async def _save_user_if_new(message: Message) -> None:
    if not message.from_user:
        return

    async with AsyncSessionLocal() as session:
        query = select(User).where(User.telegram_id == message.from_user.id)
        existing_user = await session.scalar(query)
        if existing_user:
            return

        session.add(
            User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )
        )
        await session.commit()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _save_user_if_new(message)
    first_name = message.from_user.first_name if message.from_user else "друг"
    await message.answer(
        text=(
            f"Привет, {first_name}!\n\n"
            "Я бот для заявок. Выбери действие в меню ниже."
        ),
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == BTN_CREATE_LEAD)
async def on_create_lead(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.waiting_for_name)
    await message.answer(ASK_NAME_TEXT, reply_markup=get_cancel_keyboard())


@router.message(F.text == BTN_CONTACTS)
async def on_contacts(message: Message) -> None:
    await message.answer(CONTACTS_TEXT)


@router.message(F.text == BTN_REVIEWS)
async def on_reviews(message: Message) -> None:
    await message.answer(REVIEWS_TEXT)


@router.message(F.text == BTN_CANCEL)
async def on_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(CANCEL_TEXT, reply_markup=get_main_menu_keyboard())


@router.message(LeadForm.waiting_for_name, F.text)
async def on_name_received(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("Имя не должно быть пустым. Введите имя еще раз.")
        return

    await state.update_data(name=name)
    await state.clear()
    await message.answer(
        "Имя сохранено. Продолжение формы добавим на следующем этапе.",
        reply_markup=get_main_menu_keyboard(),
    )
