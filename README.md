# Oleg_ML: Telegram-бот с RAG по Obsidian Vault

Проект: Telegram-бот, который отправляет вопросы в Flowise, а Flowise отвечает на основе заметок из Obsidian Vault.

## Архитектура

```text
Telegram -> python-telegram-bot -> Flowise API -> RAG по Obsidian Vault -> LLM
```

Компоненты:

- `Flowise` — визуальная сборка RAG-пайплайна.
- `Obsidian Vault` — база знаний в Markdown.
- `python-telegram-bot` — Telegram-интерфейс.
- `OpenRouter` — LLM API, используется внутри Flowise как OpenAI-compatible endpoint.

Vault:

```text
/home/k0st0vsk7/Documents/Obsidian Vault/my-obsidian-vault
```

В Docker он монтируется как:

```text
/vault
```

## Безопасность

В боте есть два способа ограничения доступа:

1. allowlist по Telegram ID:

```env
ALLOWED_TELEGRAM_USER_IDS=123456789,987654321
```

2. пароль через команду:

```text
/auth пароль
```

После успешной авторизации пользователь сохраняется в `data/authorized_users.json`.

Команды:

- `/start` — стартовое сообщение;
- `/help` — помощь;
- `/whoami` — показать Telegram ID;
- `/auth пароль` — авторизация по паролю;
- `/logout` — удалить локальную авторизацию.

## Запуск Flowise

```bash
cp .env.example .env
docker compose up -d
```

Открыть:

```text
http://localhost:3000
```

Логин/пароль по умолчанию:

```text
admin / admin
```

Их можно поменять в `.env`:

```env
FLOWISE_USERNAME=your_login
FLOWISE_PASSWORD=your_password
```

## Настройка Chatflow в Flowise

Создать новый Chatflow и собрать RAG:

```text
Folder with Files -> Markdown Text Splitter -> Embeddings -> Vector Store -> Conversational Retrieval QA Chain
```

Рекомендуемые настройки:

- Folder with Files:
  - Path: `/vault`
  - Recursive: enabled
  - загружать Markdown-файлы
- Markdown Text Splitter:
  - Chunk size: `500`
  - Overlap: `80`
- Vector Store:
  - FAISS или встроенное хранилище Flowise
- Chat Model:
  - OpenAI-compatible endpoint
  - Base URL: `https://openrouter.ai/api/v1`
  - API Key: OpenRouter key
  - Model: `cohere/north-mini-code:free` или другая доступная модель

Если Ollama запущена на хосте, в Docker Compose используется `network_mode: host`.
Поэтому в Flowise для Ollama можно указывать:

```text
http://127.0.0.1:11434
```

После настройки нажать:

```text
Upsert Vector Database
```

Потом взять `Chatflow ID` из URL или настроек Flowise и вставить его в `.env`:

```env
FLOWISE_CHATFLOW_ID=your_chatflow_id
FLOWISE_API_KEY=your_flowise_api_key_if_enabled
```

Проверка Flowise API:

```bash
curl -X POST "http://localhost:3000/api/v1/prediction/2fe7a9b2-8c4b-4e51-8d84-5d7358dae682" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Что такое SQL injection?",
    "overrideConfig": {
      "sessionId": "test_session"
    }
  }'
```

## Запуск Telegram-бота

Установка зависимостей:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Заполнить `.env`:

```env
TELEGRAM_TOKEN=token_from_botfather
TELEGRAM_PROXY_URL=
FLOWISE_URL=http://localhost:3000
FLOWISE_CHATFLOW_ID=2fe7a9b2-8c4b-4e51-8d84-5d7358dae682
FLOWISE_API_KEY=your_flowise_api_key_if_enabled
BOT_ACCESS_PASSWORD=your_password
ALLOWED_TELEGRAM_USER_IDS=
```

Запуск:

```bash
python -m bot.main
```

Если Telegram API доступен только через VPN или proxy, можно указать proxy:

```env
TELEGRAM_PROXY_URL=socks5://127.0.0.1:1080
```

или HTTP-proxy:

```env
TELEGRAM_PROXY_URL=http://127.0.0.1:8080
```

После изменения `.env` бот нужно перезапустить.

## Память диалога

Для каждого пользователя Telegram бот передает в Flowise отдельный `sessionId`:

```text
telegram_<user_id>
```

Если в Flowise включена память, бот будет помнить контекст отдельно для каждого пользователя.

## Форматирование ответов

Бот отправляет ответы в Telegram с HTML-разметкой. Если Flowise возвращает источники, бот добавляет их в конец сообщения.

## Возможные улучшения

- добавить Dockerfile для самого Telegram-бота;
- запускать Flowise и бота одним `docker compose`;
- добавить команды `/reset` для сброса истории;
- добавить логирование вопросов и ответов в файл;
- добавить роли пользователей: admin/user.
