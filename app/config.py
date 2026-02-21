import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV_VARS = ("BOT_TOKEN", "ADMIN_ID", "DATABASE_URL", "HOST_URL")


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} is required in .env")
    return value


def _optional_env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _parse_admin_id(raw: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError("ADMIN_ID must be an integer") from exc


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    database_url: str
    host_url: str
    webhook_secret: str | None


def load_settings() -> Settings:
    values = {name: _require_env(name) for name in REQUIRED_ENV_VARS}
    return Settings(
        bot_token=values["BOT_TOKEN"],
        admin_id=_parse_admin_id(values["ADMIN_ID"]),
        database_url=values["DATABASE_URL"],
        host_url=values["HOST_URL"].rstrip("/"),
        webhook_secret=_optional_env("WEBHOOK_SECRET"),
    )


settings = load_settings()
