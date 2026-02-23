# Lead Bot Template

Готовый Telegram-бот для приёма заявок от клиентов через форму, уведомлений админу и админ-команд.

Документ написан как рабочая инструкция для тебя: по нему можно каждый раз разворачивать нового бота под нового клиента без пропусков.

---

## 1) Что делает бот

1. Показывает меню `/start`.
2. Собирает заявку по шагам:
   - имя
   - телефон
   - услуга (необязательно)
   - комментарий (необязательно)
3. Сохраняет заявку в PostgreSQL.
4. Отправляет админу уведомление с кнопкой `✅ Обработано`.
5. Даёт админ-команды:
   - `/stats`
   - `/leads`
   - `/leads_new`
6. Шлёт напоминания по “висящим” новым заявкам.

---

## 2) Архитектура

1. Telegram -> webhook -> `POST /telegram/webhook`.
2. FastAPI принимает апдейт.
3. Aiogram Dispatcher отправляет апдейт в handlers.
4. SQLAlchemy async работает с PostgreSQL.
5. Бот крутится как web-service.

---

## 3) Технологии

1. Python 3.11
2. FastAPI
3. Aiogram 3
4. SQLAlchemy + asyncpg
5. PostgreSQL
6. Docker + docker-compose
7. Railway (деплой)

---

## 4) Важный принцип для продаж под клиентов

Для каждого клиента лучше делать отдельный деплой:

1. Отдельный Telegram Bot Token.
2. Отдельная БД (или отдельная схема/таблицы, но лучше отдельная БД).
3. Отдельный поддомен.
4. Отдельный набор переменных окружения.

Не смешивай клиентов в одном боте и одной базе.

---

## 5) Схема доменов для клиентов

У тебя базовый домен: `payflowbot.online`.

Рекомендуемая схема:

1. `client1.payflowbot.online`
2. `client2.payflowbot.online`
3. `barbershop.payflowbot.online`
4. `nailsalon.payflowbot.online`

Для каждого клиента:

1. Создаёшь CNAME/A запись в DNS.
2. Привязываешь этот поддомен к нужному Railway service.
3. В `HOST_URL` ставишь именно поддомен этого клиента.

Webhook каждого клиента:

1. `https://client1.payflowbot.online/telegram/webhook`
2. `https://client2.payflowbot.online/telegram/webhook`

---

## 6) Быстрый чек-лист перед стартом нового клиента

1. Создан новый бот в BotFather.
2. Есть новый `BOT_TOKEN`.
3. Определён `ADMIN_ID` клиента.
4. Создан отдельный сервис Railway.
5. Создана отдельная PostgreSQL база.
6. Поддомен добавлен в DNS.
7. Поддомен привязан в Railway.
8. SSL сертификат на поддомен активен.
9. `HOST_URL` соответствует поддомену.
10. Выполнена проверка `getWebhookInfo`.

---

## 7) Локальная подготовка проекта

### 7.1 Установка

1. Установи Docker Desktop.
2. Проверь:
```bash
docker --version
docker compose version
```

### 7.2 Локальный `.env` для разработки

Создай `.env`:

```env
BOT_TOKEN=your_bot_token
ADMIN_ID=123456789
HOST_URL=https://example.payflowbot.online
WEBHOOK_SECRET=your_long_random_secret

POSTGRES_USER=app_user
POSTGRES_PASSWORD=app_password
POSTGRES_DB=lead_bot_tg
POSTGRES_HOST=db
POSTGRES_PORT=5432

DATABASE_URL=postgresql+asyncpg://app_user:app_password@db:5432/lead_bot_tg
```

### 7.3 Запуск

```bash
docker compose up -d --build
docker compose ps
```

### 7.4 Логи

```bash
docker compose logs -f bot
docker compose logs -f db
```

---

## 8) Деплой в Railway (под одного клиента)

### 8.1 Создай проект

1. New Project -> Deploy from GitHub.
2. Выбери этот репозиторий.

### 8.2 Создай сервисы

1. `bot` (web service, запускает FastAPI/aiogram webhook endpoint)
2. `postgres` (Railway PostgreSQL)

### 8.3 Start Command

Если обычная команда работает:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
``` 

Если Railway не подставляет `$PORT`:

```bash
python -c "import os,uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=int(os.environ.get('PORT','8000')))"
```

### 8.4 Переменные в `bot` service

Обязательно:

1. `BOT_TOKEN`
2. `ADMIN_ID`
3. `DATABASE_URL`
4. `HOST_URL`
5. `WEBHOOK_SECRET`

Где:

1. `HOST_URL` = `https://client1.payflowbot.online`
2. `DATABASE_URL` берёшь из Railway Postgres (лучше уже в формате `postgresql://...`, код нормализует под async).

### 8.5 Поддомен в Railway

1. Settings -> Networking -> Custom Domain.
2. Добавь `client1.payflowbot.online`.
3. Railway покажет DNS запись.
4. Добавь запись в DNS-провайдере домена.
5. Дождись статуса Active/Verified.

### 8.6 Проверь health

Открой:

`https://client1.payflowbot.online/health`

Ожидается:

```json
{"status":"ok"}
```

---

## 9) Как правильно поставить webhook

Обычно webhook ставится кодом на старте сервиса.

Но для контроля полезно вручную:

```powershell
$token = "CLIENT_BOT_TOKEN"
$secret = "CLIENT_WEBHOOK_SECRET"
$url = "https://client1.payflowbot.online/telegram/webhook"

Invoke-RestMethod -Method Post "https://api.telegram.org/bot$token/setWebhook" -Body @{
  url = $url
  secret_token = $secret
  allowed_updates = '["message","callback_query"]'
}

Invoke-RestMethod "https://api.telegram.org/bot$token/getWebhookInfo" | ConvertTo-Json -Depth 6
```

Проверяешь:

1. `result.url` не пустой.
2. `result.url == https://client1.payflowbot.online/telegram/webhook`.
3. `last_error_message` пусто.

---

## 10) Обновление схемы БД при новых полях (важно)

Когда добавляешь поле в модель (например `service`), в продовой БД его тоже надо добавить.

Пример:

```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS service VARCHAR(255);
```

Если не сделать, получишь ошибку вида:

`UndefinedColumnError: column "service" of relation "leads" does not exist`.

---

## 11) Полное тестирование перед передачей клиенту

Пройди все шаги именно в таком порядке.

### 11.1 Smoke test

1. `/start` отвечает.
2. Показывается меню.

### 11.2 Форма заявки

1. Нажать `📝 Оставить заявку`.
2. Ввести имя.
3. Ввести телефон.
4. Ввести услугу (или `-`).
5. Ввести комментарий (или `-`).
6. Пользователь получил подтверждение.

### 11.3 Уведомление админу

Проверить, что админу пришло:

1. Имя
2. Телефон
3. Услуга (или `Не указана`)
4. Комментарий
5. Кнопка `✅ Обработано`

### 11.4 Админ-команды

С аккаунта админа:

1. `/stats`
2. `/leads`
3. `/leads_new`

Проверить:

1. Телефон показывается полностью.
2. Под списками есть кнопки `✅ Обработано #id`.

### 11.5 Изменение статуса

1. Нажать `✅ Обработано` у заявки.
2. Обновить `/leads_new`.
3. Заявка должна исчезнуть из новых.

### 11.6 Напоминания

1. Создать `new` заявку и не обрабатывать.
2. Дождаться проверки фоновой задачи.
3. Убедиться, что админу пришло предупреждение.

### 11.7 Логи

Проверить Railway logs:

1. Нет traceback.
2. Нет `Bad Request` от Telegram.
3. Нет ошибок БД.

---

## 12) Инструкция “подключить нового клиента” (пошагово)

### Шаг 1. Получить доступы от клиента

1. Telegram админа (ID).
2. Название/бренд (для поддомена).
3. Контакты и тексты для кнопок.

### Шаг 2. Создать бота в BotFather

1. `/newbot`
2. Получить `BOT_TOKEN`.
3. Сохранить токен в менеджер паролей.

### Шаг 3. Создать поддомен

1. Пример: `barber-msk.payflowbot.online`.
2. Добавить DNS запись.
3. Привязать Custom Domain в Railway.

### Шаг 4. Поднять отдельный Railway проект/сервис

1. Новый deploy из этого репо.
2. Подключить отдельную PostgreSQL.

### Шаг 5. Заполнить Variables

1. `BOT_TOKEN` = клиента
2. `ADMIN_ID` = клиента
3. `HOST_URL` = поддомен клиента
4. `WEBHOOK_SECRET` = новый случайный секрет
5. `DATABASE_URL` = из его Postgres

### Шаг 6. Деплой

1. Запустить deploy.
2. Проверить `/health`.

### Шаг 7. Выставить webhook и проверить

1. Выполнить `setWebhook`.
2. Проверить `getWebhookInfo`.

### Шаг 8. Пройти e2e-тест

1. `/start`
2. форма
3. уведомление админу
4. `/stats`, `/leads`, `/leads_new`
5. `✅ Обработано`

### Шаг 9. Передача клиенту

1. Отправить инструкцию по командам.
2. Отправить, как отмечать заявки обработанными.
3. Зафиксировать SLA (кто следит за ботом, как быстро реагируешь).

---

## 13) Ежедневная эксплуатация

1. Проверять Railway logs утром и вечером.
2. Проверять `getWebhookInfo` при жалобе “бот молчит”.
3. Проверять `/stats` для контроля.
4. Раз в неделю делать бэкап БД.
5. Раз в месяц менять `WEBHOOK_SECRET`.

---

## 14) Частые проблемы и быстрые решения

### Проблема: кнопки “молчат”

Проверить:

1. `getWebhookInfo.url` не пустой.
2. webhook URL совпадает с `HOST_URL + /telegram/webhook`.
3. в логах нет 403 (секрет не совпал).

### Проблема: `url` пустой в `getWebhookInfo`

1. Выполнить `setWebhook`.
2. Проверить токен.
3. Проверить, что сервис доступен по HTTPS.

### Проблема: `database ... does not exist`

1. Проверить `DATABASE_URL`.
2. Проверить, что БД реально создана.

### Проблема: `column ... does not exist`

1. Выполнить `ALTER TABLE` для новой колонки.
2. Перезапустить сервис.

### Проблема: `/stats` не отвечает админу

1. Сравнить `ADMIN_ID` с реальным Telegram ID.
2. Проверить, что пишешь команду в личке боту.

---

## 15) Безопасность

1. Никогда не коммить `.env`.
2. Не отправляй токены/пароли в чаты и скриншоты.
3. При утечке `BOT_TOKEN`:
   - в BotFather сделать `/revoke`
   - обновить переменную в Railway
4. При утечке пароля БД:
   - rotate credentials
   - обновить `DATABASE_URL`

---

## 16) Команды для работы (шпаргалка)

### Docker локально

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f bot
docker compose down
docker compose down -v
```

### Telegram webhook

```powershell
Invoke-RestMethod "https://api.telegram.org/bot$token/getWebhookInfo" | ConvertTo-Json -Depth 6
```

---

## 17) Структура проекта

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

