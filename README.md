# Lead Bot Template

Telegram-бот для сбора заявок с формой (FSM), уведомлениями администратору и статистикой.

## Функционал
- Команда `/start` и главное меню.
- Форма заявки: имя -> телефон -> комментарий.
- Кнопка `❌ Отмена` на любом шаге формы.
- Уведомление администратору о новой заявке.
- Команда `/stats` только для администратора.
- Inline-кнопка `✅ Обработано` для смены статуса заявки.

## Архитектура
1. Telegram отправляет апдейт на webhook.
2. FastAPI принимает запрос на `POST /telegram/webhook`.
3. Aiogram Dispatcher маршрутизирует апдейт в handlers.
4. Данные хранятся в PostgreSQL через SQLAlchemy async.

## Требования
- Docker Desktop
- Docker Compose
- Публичный HTTPS-домен для webhook (например, `https://www.payflowbot.online`)

## Переменные окружения
Создайте `.env` в корне проекта:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=123456789
HOST_URL=https://www.payflowbot.online
WEBHOOK_SECRET=your_random_long_secret

POSTGRES_USER=app_user
POSTGRES_PASSWORD=app_password
POSTGRES_DB=lead_bot_tg
POSTGRES_HOST=db
POSTGRES_PORT=5432

DATABASE_URL=postgresql+asyncpg://app_user:app_password@db:5432/lead_bot_tg
```

## Быстрый старт (Docker)
1. Собрать и запустить:
```bash
docker compose up -d --build
```

2. Проверить контейнеры:
```bash
docker compose ps
```

3. Проверить логи:
```bash
docker compose logs -f bot
docker compose logs -f db
```

4. Проверить health:
```text
GET http://localhost:8000/health
```

## Настройка webhook
Webhook выставляется в `app/main.py` на старте приложения, но при необходимости можно выставить вручную.

PowerShell:
```powershell
$token = "YOUR_BOT_TOKEN"
$secret = "YOUR_WEBHOOK_SECRET"
$url = "https://www.payflowbot.online/telegram/webhook"

Invoke-RestMethod -Method Post "https://api.telegram.org/bot$token/setWebhook" -Body @{
  url = $url
  secret_token = $secret
}

Invoke-RestMethod "https://api.telegram.org/bot$token/getWebhookInfo" | ConvertTo-Json -Depth 5
```

Ожидаемо:
- `result.url` не пустой
- `result.url == https://www.payflowbot.online/telegram/webhook`
- `last_error_message` пустой

## Команды и кнопки
- `/start`
- `/stats` (только `ADMIN_ID`)
- `📝 Оставить заявку`
- `📞 Контакты`
- `⭐ Отзывы`
- `❌ Отмена`
- `✅ Обработано` (в уведомлении админу)

## Сценарий полного тестирования
1. Выполнить `docker compose up -d --build`.
2. Отправить `/start` в Telegram.
3. Пройти форму `📝 Оставить заявку`:
   имя -> телефон -> комментарий.
4. Проверить, что админу пришло уведомление.
5. Проверить `/stats` с аккаунта админа.
6. Нажать `✅ Обработано` под заявкой и повторить `/stats`.
7. Проверить логи: `docker compose logs --tail=200 bot`.
8. Выполнить `docker compose down`, затем `docker compose up -d`.
9. Проверить, что данные в базе сохранились.

## Частые проблемы и решения
1. `url` пустой в `getWebhookInfo`.
Причина: webhook не выставлен.
Решение: выполнить `setWebhook` вручную.

2. `database ... does not exist`.
Причина: база не создана в volume.
Решение: `docker compose down -v` и повторный `up -d --build`, либо создать БД вручную через `psql`.

3. `inline keyboard button URL ... is invalid`.
Причина: невалидный URL в inline-кнопке.
Решение: использовать только корректные `https://...` ссылки.

4. `/stats` не отвечает админу.
Причина: `ADMIN_ID` не совпадает с реальным ID Telegram.
Решение: проверить ID и перезапустить контейнер.

## Остановка и очистка
- Остановка:
```bash
docker compose down
```
- Остановка с удалением данных:
```bash
docker compose down -v
```

## Структура проекта
```text
app/
  bot.py
  config.py
  content.py
  database.py
  main.py
  handlers/
    __init__.py
    start.py
    admin.py
  keyboards/
    menus.py
  models/
    user.py
    lead.py
  services/
    notifier.py

Dockerfile
docker-compose.yml
requirements.txt
README.md
```

## Безопасность
- Не коммитьте `.env`.
- Не публикуйте `BOT_TOKEN` и `WEBHOOK_SECRET`.
- Если токен утек, перевыпустите его через BotFather (`/revoke`).
