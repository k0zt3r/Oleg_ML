# Oleg_ML

Telegram-бот для ответов на вопросы по заметкам из Obsidian Vault.  
RAG-пайплайн собран в Flowise, а Telegram-часть написана на Python.

## Стек

- Python 3.11+
- python-telegram-bot
- Flowise
- Obsidian Vault
- Ollama Chat Model
- Ollama Embeddings
- FAISS / Vector Store в Flowise
- Docker Compose для запуска Flowise

## Как это работает

```text
Telegram
  -> Python bot
  -> Flowise Prediction API
  -> Retriever по Obsidian Vault
  -> Ollama Chat Model
  -> ответ пользователю
```

Заметки Obsidian используются как база знаний. Flowise разбивает Markdown-файлы на чанки, строит эмбеддинги через Ollama Embeddings и сохраняет их в векторное хранилище. При вопросе пользователя Flowise ищет подходящие фрагменты и передает их в локальную LLM через Ollama Chat Model.

## Структура проекта

```text
Oleg_ML/
├── bot/
│   ├── auth.py
│   ├── config.py
│   ├── flowise_client.py
│   ├── formatters.py
│   └── main.py
├── data/
│   └── .gitkeep
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

В репозиторий не добавляются `.env`, `.venv`, `flowise_data/`, `vault/` и файл локально авторизованных пользователей.

## Obsidian Vault

Локальный путь к хранилищу:

```text
путь до вашего обсидиана(лучше копировать хранилище в папку с проектом, тк FLOWISE ругается на абсолютные пути
```

В Docker Compose оно монтируется внутрь контейнера Flowise как:

```text
/vault
```

## Запуск Flowise

Сначала создать `.env`:

```bash
cp .env.example .env
```

Запустить Flowise:

```bash
docker compose up -d
```

Открыть интерфейс:

```text
http://localhost:3000
```

Логин и пароль Flowise задаются через переменные:

```env
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=admin
```

## Настройка Ollama

Для работы нужны две модели:

- модель для эмбеддингов;
- модель для генерации ответов.

Пример:

```bash
ollama pull nomic-embed-text
ollama pull qwen3.5:2b
```

Проверка:

```bash
ollama list
```

Если Flowise запущен через Docker Compose из этого проекта, он использует `network_mode: host`. Поэтому в настройках Ollama-узлов в Flowise можно указывать:

```text
http://127.0.0.1:11434
```

## Notice

В этом проекте используются локальные модели через Ollama:

- `Ollama Embeddings` для построения эмбеддингов;
- `Ollama Chat Model` для генерации ответа.

OpenRouter/OpenAI в текущей версии проекта не являются обязательными. Их можно подключить позже, если нужна более сильная модель, но для демонстрации итоговой работы достаточно локального варианта.

Если локальная модель маленькая, ответы могут быть проще и менее точными. Это нормально для учебного прототипа: основная цель проекта — показать связку Telegram + Flowise + RAG + Obsidian Vault.

## Chatflow в Flowise

В Flowise нужно создать chatflow примерно такой структуры:

```text
Folder with Files
  -> Markdown Text Splitter
  -> Ollama Embeddings
  -> Vector Store / FAISS
  -> Conversational Retrieval QA Chain
  -> Ollama Chat Model
```

Рекомендуемые настройки:

- `Folder with Files`
  - Path: `/vault`
  - Recursive: enabled
  - желательно загружать только Markdown-файлы
- `Markdown Text Splitter`
  - Chunk size: `500`
  - Overlap: `80`
- `Ollama Embeddings`
  - Base URL: `http://127.0.0.1:11434`
  - Model: `nomic-embed-text`
- `Ollama Chat Model`
  - Base URL: `http://127.0.0.1:11434`
  - Model: например `qwen2.5:1.5b`
- `Vector Store`
  - FAISS или встроенное хранилище Flowise

Пример того, как это должно выглядеть:
<img width="1147" height="843" alt="изображение" src="https://github.com/user-attachments/assets/3b50207d-ab7e-4d95-9653-6ef4d2dedc57" />

После настройки нужно нажать:

```text
Upsert Vector Database
```

После индексации можно проверить API Flowise:

```bash
curl -X POST "http://localhost:3000/api/v1/prediction/flowise_chatflow_uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Что такое SQL injection?",
    "overrideConfig": {
      "sessionId": "test_session"
    }
  }'
```

## Настройка Telegram-бота

Установить зависимости:

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
FLOWISE_CHATFLOW_ID=change_me
FLOWISE_API_KEY=

BOT_ACCESS_PASSWORD=change_me
ALLOWED_TELEGRAM_USER_IDS=

REQUEST_TIMEOUT=180
```

Запуск:

```bash
python -m bot.main
```

Если Telegram работает только через proxy/VPN, можно указать SOCKS proxy:

```env
TELEGRAM_PROXY_URL=socks5h://127.0.0.1:10808
```

`socks5h` удобен тем, что DNS-запросы тоже идут через proxy.

## Безопасность

В боте есть два простых способа ограничения доступа.

Первый способ — allowlist по Telegram ID:

```env
ALLOWED_TELEGRAM_USER_IDS=123456789,987654321
```

Второй способ — пароль:

```text
/auth пароль
```

После успешной авторизации пользователь сохраняется локально в:

```text
data/authorized_users.json
```

Этот файл не добавляется в git.

Команды бота:

- `/start` — стартовое сообщение;
- `/help` — помощь;
- `/whoami` — показать Telegram ID;
- `/auth пароль` — получить доступ;
- `/logout` — удалить локальную авторизацию.

## Память диалога

Для каждого пользователя Telegram бот передает в Flowise отдельный `sessionId`:

```text
telegram_<user_id>
```

Если в Flowise включена память, история диалога будет разделяться по пользователям.

## Пример запроса к боту

Пользователь пишет в Telegram:

```text
Что такое SQL injection?
```

Бот отправляет вопрос в Flowise, Flowise ищет релевантные заметки в Obsidian Vault и возвращает ответ на основе найденного контекста.

## Ограничения

- качество ответа зависит от локальной модели Ollama;
- если заметок мало, RAG может не найти хороший контекст;
- при большой модели ответы могут генерироваться долго;
- после изменения заметок нужно заново выполнить `Upsert Vector Database`;
- Flowise chatflow настраивается через веб-интерфейс и не хранится полностью в коде проекта.

## Возможные улучшения

- добавить Dockerfile для Telegram-бота;
- запускать Flowise и бота одним `docker compose`;
- добавить команду `/reset` для сброса истории;
- сохранять логи вопросов и ответов в файл;
- добавить роли пользователей: admin/user;
- подключить более сильную модель через OpenRouter или другой API.
