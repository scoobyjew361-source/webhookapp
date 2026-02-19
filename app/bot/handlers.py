import asyncio
from datetime import datetime, timezone
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from app.bot.keyboards import payment_links_keyboard, single_pay_keyboard
from app.bot.middleware import SubscriptionAccessMiddleware
from app.bot.payments import build_tariff_links, create_payment_link
from app.core.config import BOT_TOKEN
from app.db.database import AsyncSessionLocal
from app.db.models import Subscription, User


logger = logging.getLogger(__name__)

public_router = Router(name="public")
protected_router = Router(name="protected")
protected_router.message.middleware(SubscriptionAccessMiddleware())


async def ensure_user(telegram_id: int, username: str | None) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = select(User).where(User.telegram_id == telegram_id)
            user = (await session.execute(stmt)).scalar_one_or_none()
            if user is None:
                session.add(User(telegram_id=telegram_id, username=username))
            elif username and user.username != username:
                user.username = username


async def get_latest_subscription(telegram_id: int) -> Subscription | None:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Subscription)
            .join(User, Subscription.user_id == User.id)
            .where(User.telegram_id == telegram_id)
            .order_by(Subscription.expires_at.desc())
        )
        return (await session.execute(stmt)).scalars().first()


def is_subscription_active(subscription: Subscription | None) -> bool:
    if not subscription or not subscription.is_active or not subscription.expires_at:
        return False

    now = datetime.now(timezone.utc)
    expires_at = subscription.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return expires_at > now


@public_router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if message.from_user is None:
        return

    telegram_id = message.from_user.id
    username = message.from_user.username

    await ensure_user(telegram_id=telegram_id, username=username)

    subscription = await get_latest_subscription(telegram_id)
    if is_subscription_active(subscription):
        expires = subscription.expires_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
        await message.answer(
            "Hello! Subscription is active.\n"
            f"Access is open until: {expires}\n"
            "Commands: /pay, /status"
        )
        return

    try:
        pay_url = await create_payment_link(telegram_id=telegram_id, username=username, plan_id="basic")
        await message.answer(
            "Hello! Subscription is inactive.\n"
            "Tap the button to open access:",
            reply_markup=single_pay_keyboard(pay_url, text="Pay"),
        )
    except Exception:
        await message.answer("Hello! Subscription is inactive. Use /pay to choose a plan.")


@public_router.message(Command("pay"))
async def cmd_pay(message: Message) -> None:
    if message.from_user is None:
        return

    telegram_id = message.from_user.id
    username = message.from_user.username

    try:
        links = await build_tariff_links(telegram_id=telegram_id, username=username)
    except Exception as exc:
        logger.exception("Cannot build tariff links: %s", exc)
        await message.answer("Could not prepare payment links. Try again in a minute.")
        return

    await message.answer("Choose a plan:", reply_markup=payment_links_keyboard(links))


@public_router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    if message.from_user is None:
        return

    telegram_id = message.from_user.id
    username = message.from_user.username

    subscription = await get_latest_subscription(telegram_id)
    if is_subscription_active(subscription):
        expires = subscription.expires_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
        await message.answer(f"Subscription is active until: {expires}")
        return

    try:
        pay_url = await create_payment_link(telegram_id=telegram_id, username=username, plan_id="basic")
        await message.answer(
            "Subscription is inactive.",
            reply_markup=single_pay_keyboard(pay_url, text="Pay"),
        )
    except Exception:
        await message.answer("Subscription is inactive. Use /pay to continue.")


@protected_router.message(Command("content"))
async def cmd_content(message: Message) -> None:
    await message.answer("Private content for active subscribers.")


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(public_router)
    dp.include_router(protected_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
