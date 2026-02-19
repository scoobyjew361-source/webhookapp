from pydantic import BaseModel, Field


class PaymentCreateIn(BaseModel):
    telegram_id: int = Field(..., gt=0)
    username: str | None = None
    plan_id: str = Field(..., pattern="^(basic|pro)$")


class PaymentCreateOut(BaseModel):
    payment_url: str
    plan_id: str
