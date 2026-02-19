from datetime import timezone, datetime
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy import select

from app.bot.keyboards import single_pay_keyboard
from app.bot.payments import create_payment_link
from app.db.database import AsyncSessionLocal
from app.db.models import Subscription, User


class SubscriptionAccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if event.from_user is None:
            return await handler(event, data)

        telegram_id = event.from_user.id

        async with AsyncSessionLocal() as session:
            stmt = (
                select(Subscription)
                .join(User, Subscription.user_id == User.id)
                .where(User.telegram_id == telegram_id)
                .order_by(Subscription.expires_at.desc())
            )
            subscription = (await session.execute(stmt)).scalars().first()

        now = datetime.now(timezone.utc)
        if subscription and subscription.is_active and subscription.expires_at:
            expires_at = subscription.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > now:
                return await handler(event, data)

        try:
            pay_url = await create_payment_link(
                telegram_id=telegram_id,
                username=event.from_user.username,
                plan_id="basic",
            )
            await event.answer(
                "Access requires an active subscription. Tap the button to pay:",
                reply_markup=single_pay_keyboard(pay_url, text="Pay"),
            )
        except Exception:
            await event.answer("Access requires subscription. Use /pay to continue.")

        return None
