from aiogram import Bot, Dispatcher

from app.config import settings
from app.handlers import router as root_router

bot = Bot(token=settings.bot_token)
dp = Dispatcher()
dp.include_router(root_router)
