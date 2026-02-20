from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Оставить заявку")],
            [KeyboardButton(text="📞 Контакты")],
            [KeyboardButton(text="⭐ Отзывы")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_admin_lead_keyboard(phone: str, lead_id: int) -> InlineKeyboardMarkup:
    clean_phone = phone.replace(" ", "")
    if not clean_phone.startswith("+"):
        clean_phone = f"+{clean_phone}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📞 Позвонить", url=f"tel:{clean_phone}")],
            [InlineKeyboardButton(text="✅ Обработано", callback_data=f"lead_done:{lead_id}")],
        ]
    )
