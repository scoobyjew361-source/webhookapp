from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_links_keyboard(links: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for title, url in links:
        builder.button(text=title, url=url)
    builder.adjust(1)
    return builder.as_markup()


def single_pay_keyboard(url: str, text: str = "Pay") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=text, url=url)
    return builder.as_markup()
