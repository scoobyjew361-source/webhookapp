def extract_update_id(payload: dict) -> int | None:
    update_id = payload.get("update_id")
    return update_id if isinstance(update_id, int) else None


def parse_lead_id_from_callback(data: str | None) -> int | None:
    if not data or ":" not in data:
        return None
    lead_id_raw = data.split(":", 1)[1]
    try:
        return int(lead_id_raw)
    except ValueError:
        return None


def normalize_phone(phone: str) -> str:
    cleaned = (
        phone.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )
    if cleaned and not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"
    return cleaned
