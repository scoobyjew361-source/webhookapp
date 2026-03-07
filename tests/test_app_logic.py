from pathlib import Path

import pytest

from app.config import _parse_admin_id, _require_env
from app.utils.logic import extract_update_id, normalize_phone, parse_lead_id_from_callback


def test_parse_admin_id_success() -> None:
    assert _parse_admin_id("123456") == 123456


def test_parse_admin_id_invalid() -> None:
    with pytest.raises(RuntimeError, match="ADMIN_ID must be an integer"):
        _parse_admin_id("abc")


def test_require_env_returns_trimmed_value(monkeypatch) -> None:
    monkeypatch.setenv("TEST_KEY", "  value  ")
    assert _require_env("TEST_KEY") == "value"


def test_require_env_raises_on_empty(monkeypatch) -> None:
    monkeypatch.setenv("EMPTY_KEY", "   ")
    with pytest.raises(RuntimeError, match="Environment variable EMPTY_KEY is required in .env"):
        _require_env("EMPTY_KEY")


def test_parse_lead_id_from_callback_success() -> None:
    assert parse_lead_id_from_callback("lead_done:42") == 42


def test_parse_lead_id_from_callback_invalid() -> None:
    assert parse_lead_id_from_callback(None) is None
    assert parse_lead_id_from_callback("lead_done:not_a_number") is None
    assert parse_lead_id_from_callback("bad_format") is None


def test_normalize_phone_adds_plus_and_strips_symbols() -> None:
    assert normalize_phone("8 (999) 111-22-33") == "+89991112233"


def test_extract_update_id() -> None:
    assert extract_update_id({"update_id": 101}) == 101
    assert extract_update_id({"update_id": "101"}) is None
    assert extract_update_id({}) is None


def test_migration_for_processed_updates_exists() -> None:
    migration = Path("alembic/versions/0003_add_processed_updates_and_reminder_fields.py")
    assert migration.exists()
    text = migration.read_text(encoding="utf-8")
    assert "processed_updates" in text
