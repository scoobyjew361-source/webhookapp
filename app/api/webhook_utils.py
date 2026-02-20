def extract_status(payload: dict) -> str:
    raw = (
        payload.get("status")
        or payload.get("invoiceStatus")
        or payload.get("data", {}).get("status")
        or ""
    )
    return str(raw).lower().strip()


def extract_transaction_id(payload: dict) -> str:
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
