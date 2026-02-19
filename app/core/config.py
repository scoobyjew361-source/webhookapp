import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "app_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "app_pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "app_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
LAVA_SECRET_KEY = os.getenv("LAVA_SECRET_KEY", "")
LAVA_SHOP_ID = os.getenv("LAVA_SHOP_ID", "")
HOST_URL = os.getenv("HOST_URL", "http://localhost:8000")
LAVA_API_URL = os.getenv("LAVA_API_URL", "https://api.lava.ru")
LAVA_WEBHOOK_KEY = os.getenv("LAVA_WEBHOOK_KEY", "")
API_INTERNAL_URL = os.getenv("API_INTERNAL_URL", "http://api:8000")
