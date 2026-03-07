from datetime import UTC, datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import case, func, or_, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.lead import Lead
from app.models.user import User
from app.utils.logic import parse_lead_id_from_callback

router = Router()
STALE_AFTER_HOURS = 1
REMINDER_REPEAT_HOURS = 3


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id) and user_id == settings.admin_id


def _time_ago_text(created_at: datetime) -> str:
    now = datetime.now(UTC)
    dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
    delta = now - dt

    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} h ago"

    days = hours // 24
    return f"{days} d ago"


def _format_lead_line(index: int, lead: Lead) -> str:
    age = _time_ago_text(lead.created_at)
    stale = datetime.now(UTC) - (
        lead.created_at if lead.created_at.tzinfo else lead.created_at.replace(tzinfo=UTC)
    ) > timedelta(hours=3)
    warning = " [STALE]" if stale else ""
    service_text = lead.service.strip() if lead.service and lead.service.strip() else "Not provided"
    return (
        f"{index}. {lead.name} {lead.phone} ({age}){warning}\n"
        f"   Service: {service_text}"
    )


def _build_leads_keyboard(leads: list[Lead]) -> InlineKeyboardMarkup | None:
    new_leads = [lead for lead in leads if lead.status == "new"]
    if not new_leads:
        return None

    rows = [
        [
            InlineKeyboardButton(
                text=f"Done #{lead.id}",
                callback_data=f"lead_done:{lead.id}",
            )
        ]
        for lead in new_leads
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
        "Stats:\n\n"
        f"Users: {users_count}\n"
        f"Total leads: {leads_total}\n"
        f"New: {leads_new}\n"
        f"Completed: {leads_completed}"
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
        await message.answer("No leads yet.")
        return

    lines = ["Latest leads:\n"]
    for idx, lead in enumerate(leads, start=1):
        status = "New" if lead.status == "new" else "Completed"
        lines.append(f"{_format_lead_line(idx, lead)}\n   Status: {status}\n")

    keyboard = _build_leads_keyboard(leads)
    await message.answer("\n".join(lines), reply_markup=keyboard)


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
        await message.answer("No pending leads.")
        return

    lines = [f"Pending leads ({len(leads)}):\n"]
    for idx, lead in enumerate(leads, start=1):
        lines.append(_format_lead_line(idx, lead))
        lines.append("")

    keyboard = _build_leads_keyboard(leads)
    await message.answer("\n".join(lines).strip(), reply_markup=keyboard)


@router.callback_query(F.data.startswith("lead_done:"))
async def on_lead_done(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id if callback.from_user else None):
        await callback.answer()
        return

    lead_id = parse_lead_id_from_callback(callback.data)
    if lead_id is None:
        await callback.answer("Invalid lead ID", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        lead = await session.get(Lead, lead_id)
        if not lead:
            await callback.answer("Lead not found", show_alert=True)
            return

        lead.status = "completed"
        lead.last_reminder_at = None
        await session.commit()

    await callback.answer("Lead marked as completed")


async def send_stale_lead_reminders(bot: Bot) -> None:
    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(hours=STALE_AFTER_HOURS)
    repeat_cutoff = now - timedelta(hours=REMINDER_REPEAT_HOURS)

    async with AsyncSessionLocal() as session:
        overdue_leads = (
            await session.scalars(
                select(Lead)
                .where(
                    Lead.status == "new",
                    Lead.created_at <= stale_cutoff,
                    or_(Lead.last_reminder_at.is_(None), Lead.last_reminder_at <= repeat_cutoff),
                )
                .order_by(Lead.created_at.asc())
            )
        ).all()

        for lead in overdue_leads:
            age = _time_ago_text(lead.created_at)
            await bot.send_message(
                chat_id=settings.admin_id,
                text=f"Stale lead from {lead.name}: waiting {age}.",
            )
            lead.last_reminder_at = now
            lead.reminder_count += 1

        if overdue_leads:
            await session.commit()
