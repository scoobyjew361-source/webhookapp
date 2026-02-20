from aiogram import Bot
from aiogram.enums import ParseMode

from app.config import settings
from app.keyboards.menus import get_admin_lead_keyboard


def build_admin_lead_message(
    name: str,
    phone: str,
    comment: str | None,
    username: str | None,
) -> str:
    username_text = f"@{username}" if username else "не указан"
    comment_text = comment.strip() if comment and comment.strip() else "без комментария"

    return (
        "🔔 <b>Новая заявка</b>\n\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"📱 <b>Телефон:</b> {phone}\n"
        f"💬 <b>Комментарий:</b> {comment_text}\n"
        f"🙋 <b>Telegram:</b> {username_text}"
    )


async def notify_admin_about_lead(
    bot: Bot,
    lead_id: int,
    name: str,
    phone: str,
    comment: str | None = None,
    username: str | None = None,
) -> None:
    text = build_admin_lead_message(
        name=name,
        phone=phone,
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
