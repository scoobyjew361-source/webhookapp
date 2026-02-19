import json
import hmac
import hashlib
import logging
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping

import httpx


class LavaService:
    def __init__(
        self,
        api_url: str,
        shop_id: str,
        secret_key: str,
        webhook_key: str,
        host_url: str,
        timeout: float = 15.0,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.webhook_key = webhook_key
        self.host_url = host_url.rstrip("/")
        self.timeout = timeout

        self.logger = logging.getLogger("lava")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            fh = logging.FileHandler("lava.log", encoding="utf-8")
            fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            fh.setFormatter(fmt)
            self.logger.addHandler(fh)

    @staticmethod
    def _to_lava_sum(amount: Decimal | str | float | int) -> float:
        v = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(v)

    @staticmethod
    def _sign(body_json: str, key: str) -> str:
        return hmac.new(
            key.encode("utf-8"),
            body_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def create_payment(
        self,
        amount: Decimal | str | float | int,
        user_id: int,
        description: str,
    ) -> dict[str, str]:
        order_id = f"user-{user_id}-{int(time.time())}"

        payload: dict[str, Any] = {
            "shopId": self.shop_id,
            "sum": self._to_lava_sum(amount),
            "orderId": order_id,
            "hookUrl": f"{self.host_url}/api/webhook/lava",
            "successUrl": f"{self.host_url}/pay/success",
            "failUrl": f"{self.host_url}/pay/fail",
            "customFields": {
                "user_id": str(user_id),
                "description": description,
            },
        }

        body_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        signature = self._sign(body_json, self.secret_key)

        url = f"{self.api_url}/business/invoice/create"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Signature": signature,
        }

        self.logger.info("REQ %s body=%s", url, body_json)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, content=body_json.encode("utf-8"), headers=headers)

        self.logger.info("RES status=%s body=%s", resp.status_code, resp.text)
        resp.raise_for_status()

        data = resp.json()

        payment_url = (
            data.get("data", {}).get("url")
            or data.get("data", {}).get("payUrl")
            or data.get("url")
        )
        if not payment_url:
            raise ValueError(f"Lava response has no payment url: {data}")

        transaction_id = (
            data.get("data", {}).get("invoiceId")
            or data.get("invoiceId")
            or data.get("data", {}).get("id")
            or data.get("id")
            or order_id
        )

        return {
            "payment_url": str(payment_url),
            "transaction_id": str(transaction_id),
            "order_id": order_id,
        }

    def verify_signature(self, headers: Mapping[str, str], body: bytes) -> bool:
        normalized_headers = {k.lower(): v for k, v in headers.items()}
        received = normalized_headers.get("signature", "")
        expected = hmac.new(
            self.webhook_key.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(received, expected)
