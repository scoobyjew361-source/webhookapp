import logging
from datetime import datetime

logger = logging.getLogger("bot_events")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("bot_events.log", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

async def send_payment_success_event(telegram_id: int, expires_at: datetime) -> None:
    logger.info("payment_success telegram_id=%s expires_at=%s", telegram_id, expires_at.isoformat())