import asyncio
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError

from app.bot import bot, dp
from app.config import settings
from app.database import AsyncSessionLocal, run_migrations
from app.handlers.admin import send_stale_lead_reminders
from app.models.processed_update import ProcessedUpdate
from app.utils.logic import extract_update_id

WEBHOOK_PATH = "/telegram/webhook"
WEBHOOK_URL = f"{settings.host_url}{WEBHOOK_PATH}"


async def _reminder_loop() -> None:
    while True:
        await send_stale_lead_reminders(bot)
        await asyncio.sleep(30 * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(run_migrations)
    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=settings.webhook_secret,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    reminder_task = asyncio.create_task(_reminder_loop())
    yield
    reminder_task.cancel()
    try:
        await reminder_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(WEBHOOK_PATH)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    if x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid telegram webhook secret")

    payload = await request.json()
    update_id = extract_update_id(payload)
    if update_id is None:
        raise HTTPException(status_code=400, detail="Invalid telegram payload: missing update_id")

    async with AsyncSessionLocal() as session:
        session.add(ProcessedUpdate(update_id=update_id))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            # Telegram can retry the same update. Ignore duplicates.
            return {"ok": True}

    update = Update.model_validate(payload)
    await dp.feed_update(bot, update)
    return {"ok": True}
