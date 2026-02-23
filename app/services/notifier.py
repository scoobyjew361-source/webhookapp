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
    service_text = service.strip() if service and service.strip() else "Не указана"
    comment_text = comment.strip() if comment and comment.strip() else "Нет"
    username_text = f"@{username}" if username else "Не указан"

    return (
        f"<code>{lead_id:08d}</code>\n"
        "📩 <b>НОВАЯ ЗАЯВКА!</b>\n\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"📱 <b>Телефон:</b> {phone}\n"
        f"💇 <b>Услуга:</b> {service_text}\n"
        f"💬 <b>Комментарий:</b> {comment_text}\n"
        f"👤 <b>Telegram:</b> {username_text}"
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
