from app.api.webhook_utils import extract_status, extract_transaction_id
from app.services.plans import PLAN_PERIODS_DAYS


def test_extract_status_from_top_level() -> None:
    assert extract_status({"status": "SUCCESS"}) == "success"


def test_extract_status_from_nested_data() -> None:
    payload = {"data": {"status": "failed"}}
    assert extract_status(payload) == "failed"


def test_extract_transaction_id_priorities() -> None:
    payload = {"invoiceId": "inv-123", "id": "fallback"}
    assert extract_transaction_id(payload) == "inv-123"


def test_extract_transaction_id_from_nested_data() -> None:
    payload = {"data": {"invoiceId": "nested-42"}}
    assert extract_transaction_id(payload) == "nested-42"


def test_plan_period_days() -> None:
    assert PLAN_PERIODS_DAYS["basic"] == 30
    assert PLAN_PERIODS_DAYS["pro"] == 90
