import pytest

from app.config import _parse_admin_id, _require_env


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
