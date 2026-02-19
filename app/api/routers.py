from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import PaymentCreateIn, PaymentCreateOut
from app.core.config import HOST_URL, LAVA_API_URL, LAVA_SECRET_KEY, LAVA_SHOP_ID, LAVA_WEBHOOK_KEY
from app.db.database import get_db
from app.db.models import Payment, Subscription, User
from app.services.lava import LavaService
from app.services.notifications import send_payment_success_event


router = APIRouter(prefix="/api", tags=["api"])
log = logging.getLogger("webhook")


lava_service = LavaService(
    api_url=LAVA_API_URL,
    shop_id=LAVA_SHOP_ID,
    secret_key=LAVA_SECRET_KEY,
    webhook_key=LAVA_WEBHOOK_KEY,
    host_url=HOST_URL,
)

PLAN_PRICES: dict[str, Decimal] = {
    "basic": Decimal("299.00"),
    "pro": Decimal("799.00"),
}


def _extract_status(payload: dict) -> str:
    raw = (
        payload.get("status")
        or payload.get("invoiceStatus")
        or payload.get("data", {}).get("status")
        or ""
    )
    return str(raw).lower().strip()


def _extract_transaction_id(payload: dict) -> str:
    raw = (
        payload.get("transaction_id")
        or payload.get("invoiceId")
        or payload.get("id")
        or payload.get("orderId")
        or payload.get("data", {}).get("invoiceId")
        or payload.get("data", {}).get("id")
        or ""
    )
    return str(raw).strip()


@router.post("/payments/create", response_model=PaymentCreateOut)
async def create_payment(payload: PaymentCreateIn, db: AsyncSession = Depends(get_db)):
    amount = PLAN_PRICES.get(payload.plan_id)
    if amount is None:
        raise HTTPException(status_code=400, detail="Unsupported plan_id")

    async with db.begin():
        user_stmt = select(User).where(User.telegram_id == payload.telegram_id)
        user = (await db.execute(user_stmt)).scalar_one_or_none()

        if user is None:
            user = User(telegram_id=payload.telegram_id, username=payload.username)
            db.add(user)
            await db.flush()
        elif payload.username and user.username != payload.username:
            user.username = payload.username

        user_id = user.id

    payment_data = await lava_service.create_payment(
        amount=amount,
        user_id=user_id,
        description=f"{payload.plan_id} subscription",
    )

    async with db.begin():
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency="RUB",
            status="pending",
            transaction_id=payment_data["transaction_id"],
        )
        db.add(payment)

    return PaymentCreateOut(payment_url=payment_data["payment_url"], plan_id=payload.plan_id)


@router.post("/webhook/lava")
async def lava_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()

    if not lava_service.verify_signature(request.headers, body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    status = _extract_status(payload)
    transaction_id = _extract_transaction_id(payload)

    if not transaction_id:
        raise HTTPException(status_code=400, detail="transaction_id is required")

    async with db.begin():
        stmt = (
            select(Payment)
            .where(Payment.transaction_id == transaction_id)
            .with_for_update()
        )
        payment = (await db.execute(stmt)).scalar_one_or_none()

        if payment is None:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment.status == "success":
            return {"ok": True, "idempotent": True, "status": "already_success"}

        if status == "success":
            payment.status = "success"

            sub_stmt = (
                select(Subscription)
                .where(Subscription.user_id == payment.user_id)
                .with_for_update()
            )
            sub = (await db.execute(sub_stmt)).scalar_one_or_none()

            now = datetime.now(timezone.utc)
            period = timedelta(days=30)

            if sub is None:
                sub = Subscription(
                    user_id=payment.user_id,
                    plan_id="basic",
                    expires_at=now + period,
                    is_active=True,
                )
                db.add(sub)
            else:
                base = sub.expires_at if sub.expires_at and sub.expires_at > now else now
                sub.expires_at = base + period
                sub.is_active = True

            user_stmt = select(User).where(User.id == payment.user_id)
            user = (await db.execute(user_stmt)).scalar_one_or_none()

        elif status in {"failed", "cancelled", "canceled", "expired"}:
            payment.status = "failed"
            return {"ok": True, "status": "failed_updated"}
        else:
            return {"ok": True, "status": "ignored_unknown_status", "raw_status": status}

    if status == "success":
        sub_stmt = select(Subscription).where(Subscription.user_id == payment.user_id)
        sub = (await db.execute(sub_stmt)).scalar_one()
        user_stmt = select(User).where(User.id == payment.user_id)
        user = (await db.execute(user_stmt)).scalar_one_or_none()
        if user:
            await send_payment_success_event(user.telegram_id, sub.expires_at)

    return {"ok": True, "status": "success_processed"}
