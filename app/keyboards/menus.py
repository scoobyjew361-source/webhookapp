from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.content import BTN_CANCEL, BTN_CONTACTS, BTN_CREATE_LEAD, BTN_REVIEWS
from app.utils.logic import normalize_phone


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CREATE_LEAD)],
            [KeyboardButton(text=BTN_CONTACTS)],
            [KeyboardButton(text=BTN_REVIEWS)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_admin_lead_keyboard(phone: str, lead_id: int) -> InlineKeyboardMarkup:
    phone_link = normalize_phone(phone)
    whatsapp_link = f"https://wa.me/{phone_link.replace('+', '')}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Call", url=whatsapp_link)],
            [InlineKeyboardButton(text="Done", callback_data=f"lead_done:{lead_id}")],
        ]
    )
