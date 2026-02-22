from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.lead import Lead
from app.models.user import User

router = Router()


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id) and user_id == settings.admin_id


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

    await callback.answer("Заявка отмечена как обработанная")
