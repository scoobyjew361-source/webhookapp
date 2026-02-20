import logging
from datetime import datetime, timezone

import httpx

from app.core.config import BOT_TOKEN

logger = logging.getLogger("bot_events")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("bot_events.log", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)


async def send_payment_success_event(telegram_id: int, expires_at: datetime) -> None:
    logger.info("payment_success telegram_id=%s expires_at=%s", telegram_id, expires_at.isoformat())

    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN is empty, skipping Telegram notification")
        return

    normalized = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
    expires_text = normalized.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    text = (
        "Payment received. Subscription is active.\n"
        f"Access is open until: {expires_text}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
        response.raise_for_status()
    except Exception:
        logger.exception("Failed to send Telegram notification to telegram_id=%s", telegram_id)
