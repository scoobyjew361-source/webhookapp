from datetime import UTC, datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import case, func, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.lead import Lead
from app.models.user import User

router = Router()
_reminded_lead_ids: set[int] = set()


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id) and user_id == settings.admin_id


def _time_ago_text(created_at: datetime) -> str:
    now = datetime.now(UTC)
    dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
    delta = now - dt

    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "только что"
    if minutes < 60:
        return f"{minutes} мин назад"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} час назад" if hours == 1 else f"{hours} ч назад"

    days = hours // 24
    return f"{days} дн назад"


def _mask_phone(phone: str) -> str:
    normalized = "".join(ch for ch in phone if ch.isdigit() or ch == "+")
    if len(normalized) <= 6:
        return phone
    return f"{normalized[:5]}..."


def _format_lead_line(index: int, lead: Lead) -> str:
    age = _time_ago_text(lead.created_at)
    warning = " ⚠️" if datetime.now(UTC) - (lead.created_at if lead.created_at.tzinfo else lead.created_at.replace(tzinfo=UTC)) > timedelta(hours=3) else ""
    service_text = lead.service.strip() if lead.service and lead.service.strip() else "Не указана"
    return (
        f"{index}. {lead.name} {_mask_phone(lead.phone)} ({age}){warning}\n"
        f"   Услуга: {service_text}"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return

    async with AsyncSessionLocal() as session:
        users_count = await session.scalar(select(func.count()).select_from(User)) or 0
        leads_total = await session.scalar(select(func.count()).select_from(Lead)) or 0
        leads_new = await session.scalar(
            select(func.count()).select_from(Lead).where(Lead.status == "new")
        ) or 0
        leads_completed = await session.scalar(
            select(func.count()).select_from(Lead).where(Lead.status == "completed")
        ) or 0

    text = (
        "📊 Статистика:\n\n"
        f"Пользователей: {users_count}\n"
        f"Заявок всего: {leads_total}\n"
        f"Новых: {leads_new}\n"
        f"Обработанных: {leads_completed}"
    )
    await message.answer(text)


@router.message(Command("leads"))
async def cmd_leads(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return

    async with AsyncSessionLocal() as session:
        leads = (
            await session.scalars(
                select(Lead)
                .order_by(
                    case((Lead.status == "new", 0), else_=1),
                    Lead.created_at.desc(),
                )
                .limit(10)
            )
        ).all()

    if not leads:
        await message.answer("📋 Заявок пока нет.")
        return

    lines = ["📋 Последние заявки:\n"]
    for idx, lead in enumerate(leads, start=1):
        status = "Новая" if lead.status == "new" else "Обработана"
        lines.append(f"{_format_lead_line(idx, lead)}\n   Статус: {status}\n")

    await message.answer("\n".join(lines))


@router.message(Command("leads_new"))
async def cmd_leads_new(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        return

    async with AsyncSessionLocal() as session:
        leads = (
            await session.scalars(
                select(Lead)
                .where(Lead.status == "new")
                .order_by(Lead.created_at.asc())
                .limit(50)
            )
        ).all()

    if not leads:
        await message.answer("📋 Необработанных заявок нет.")
        return

    lines = [f"📋 Необработанные заявки ({len(leads)}):\n"]
    for idx, lead in enumerate(leads, start=1):
        lines.append(_format_lead_line(idx, lead))
        lines.append("")

    await message.answer("\n".join(lines).strip())


@router.callback_query(F.data.startswith("lead_done:"))
async def on_lead_done(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer()
        return

    lead_id_raw = (callback.data or "").split(":", 1)[1]
    try:
        lead_id = int(lead_id_raw)
    except ValueError:
        await callback.answer("Некорректный ID заявки", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        lead = await session.get(Lead, lead_id)
        if not lead:
            await callback.answer("Заявка не найдена", show_alert=True)
            return

        lead.status = "completed"
        await session.commit()

    _reminded_lead_ids.discard(lead_id)
    await callback.answer("Заявка отмечена как обработанная")


async def send_stale_lead_reminders(bot: Bot) -> None:
    cutoff = datetime.now(UTC) - timedelta(hours=1)

    async with AsyncSessionLocal() as session:
        overdue_leads = (
            await session.scalars(
                select(Lead)
                .where(Lead.status == "new", Lead.created_at <= cutoff)
                .order_by(Lead.created_at.asc())
            )
        ).all()

    current_overdue_ids = {lead.id for lead in overdue_leads}
    _reminded_lead_ids.intersection_update(current_overdue_ids)

    for lead in overdue_leads:
        if lead.id in _reminded_lead_ids:
            continue
        age = _time_ago_text(lead.created_at)
        await bot.send_message(
            chat_id=settings.admin_id,
            text=f"⚠️ Заявка от {lead.name} висит {age}! Клиент ждёт звонка.",
        )
        _reminded_lead_ids.add(lead.id)
