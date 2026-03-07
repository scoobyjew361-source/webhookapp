from html import escape

from aiogram import Bot
from aiogram.enums import ParseMode

from app.config import settings
from app.keyboards.menus import get_admin_lead_keyboard


def build_admin_lead_message(
    lead_id: int,
    name: str,
    phone: str,
    service: str | None,
    comment: str | None,
    username: str | None,
) -> str:
    safe_name = escape(name)
    safe_phone = escape(phone)
    service_text = escape(service.strip()) if service and service.strip() else "Not provided"
    comment_text = escape(comment.strip()) if comment and comment.strip() else "None"
    username_text = escape(f"@{username}") if username else "Not provided"

    return (
        f"<code>{lead_id:08d}</code>\n"
        "<b>NEW LEAD</b>\n\n"
        f"<b>Name:</b> {safe_name}\n"
        f"<b>Phone:</b> {safe_phone}\n"
        f"<b>Service:</b> {service_text}\n"
        f"<b>Comment:</b> {comment_text}\n"
        f"<b>Telegram:</b> {username_text}"
    )


async def notify_admin_about_lead(
    bot: Bot,
    lead_id: int,
    name: str,
    phone: str,
    service: str | None = None,
    comment: str | None = None,
    username: str | None = None,
) -> None:
    text = build_admin_lead_message(
        lead_id=lead_id,
        name=name,
        phone=phone,
        service=service,
        comment=comment,
        username=username,
    )
    keyboard = get_admin_lead_keyboard(phone=phone, lead_id=lead_id)

    await bot.send_message(
        chat_id=settings.admin_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
