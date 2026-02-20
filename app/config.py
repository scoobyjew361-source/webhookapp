import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Переменная окружения {name} не задана в .env")
    return value


def _parse_admin_id(raw: str) -> int:
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError("ADMIN_ID должен быть целым числом") from exc


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    database_url: str
    host_url: str


def load_settings() -> Settings:
    bot_token = _require_env("BOT_TOKEN")
    admin_id_raw = _require_env("ADMIN_ID")
    database_url = _require_env("DATABASE_URL")
    host_url = _require_env("HOST_URL")

    return Settings(
        bot_token=bot_token,
        admin_id=_parse_admin_id(admin_id_raw),
        database_url=database_url,
        host_url=host_url,
    )


settings = load_settings()
