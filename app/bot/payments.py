from dataclasses import dataclass

import httpx

from app.core.config import API_INTERNAL_URL


@dataclass(frozen=True)
class Tariff:
    plan_id: str
    title: str


TARIFFS: tuple[Tariff, ...] = (
    Tariff(plan_id="basic", title="Basic: 30 days - 299 RUB"),
    Tariff(plan_id="pro", title="Pro: 90 days - 799 RUB"),
)


async def create_payment_link(telegram_id: int, username: str | None, plan_id: str) -> str:
    payload = {
        "telegram_id": telegram_id,
        "username": username,
        "plan_id": plan_id,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(f"{API_INTERNAL_URL}/api/payments/create", json=payload)

    if response.status_code >= 400:
        raise RuntimeError(f"Cannot create payment link: {response.status_code} {response.text}")

    data = response.json()
    payment_url = data.get("payment_url")
    if not payment_url:
        raise RuntimeError("Payment API did not return payment_url")

    return str(payment_url)


async def build_tariff_links(telegram_id: int, username: str | None) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for tariff in TARIFFS:
        url = await create_payment_link(telegram_id=telegram_id, username=username, plan_id=tariff.plan_id)
        links.append((tariff.title, url))
    return links
