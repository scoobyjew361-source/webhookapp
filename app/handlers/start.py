from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select

from app.content import (
    ASK_COMMENT_TEXT,
    ASK_NAME_TEXT,
    ASK_PHONE_TEXT,
    BTN_CANCEL,
    BTN_CONTACTS,
    BTN_CREATE_LEAD,
    BTN_REVIEWS,
    CANCEL_TEXT,
    CONTACTS_TEXT,
    LEAD_SAVED_TEXT,
    REVIEWS_TEXT,
)
from app.database import AsyncSessionLocal
from app.keyboards.menus import get_cancel_keyboard, get_main_menu_keyboard
from app.models.lead import Lead
from app.models.user import User

router = Router()


class LeadForm(StatesGroup):
    name = State()
    phone = State()
    comment = State()


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
    await state.set_state(LeadForm.name)
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


@router.message(LeadForm.name, F.text)
async def on_name_received(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("Имя не должно быть пустым. Введите имя еще раз.")
        return

    await state.update_data(name=name)
    await state.set_state(LeadForm.phone)
    await message.answer(ASK_PHONE_TEXT, reply_markup=get_cancel_keyboard())


@router.message(LeadForm.phone, F.text)
async def on_phone_received(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not phone:
        await message.answer("Телефон не должен быть пустым. Введите телефон еще раз.")
        return

    await state.update_data(phone=phone)
    await state.set_state(LeadForm.comment)
    await message.answer(ASK_COMMENT_TEXT, reply_markup=get_cancel_keyboard())


@router.message(LeadForm.comment, F.text)
async def on_comment_received(message: Message, state: FSMContext) -> None:
    comment_raw = message.text.strip()
    comment = None if comment_raw in {"", "-"} else comment_raw

    data = await state.get_data()
    name = data.get("name")
    phone = data.get("phone")
    if not name or not phone or not message.from_user:
        await state.clear()
        await message.answer(
            "Не удалось сохранить заявку. Пожалуйста, начните заново.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    await _save_user_if_new(message)

    async with AsyncSessionLocal() as session:
        lead = Lead(
            user_id=message.from_user.id,
            name=name,
            phone=phone,
            comment=comment,
        )
        session.add(lead)
        await session.commit()
        await session.refresh(lead)

    from app.bot import bot
    from app.services.notifier import notify_admin_about_lead

    await notify_admin_about_lead(
        bot=bot,
        lead_id=lead.id,
        name=name,
        phone=phone,
        comment=comment,
        username=message.from_user.username,
    )

    await state.clear()
    await message.answer(LEAD_SAVED_TEXT, reply_markup=get_main_menu_keyboard())
