import logging

import httpx
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError, TimedOut
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from bot.auth import authorize_by_password, is_allowed, logout_user
from bot.config import FLOWISE_CHATFLOW_ID, FLOWISE_URL, TELEGRAM_PROXY_URL, TELEGRAM_TOKEN
from bot.flowise_client import ask_flowise
from bot.formatters import format_answer


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("oleg-ml-bot")
logging.getLogger("httpx").setLevel(logging.WARNING)


def get_user_id(update: Update) -> int:
    """Возвращает Telegram user id."""
    return update.effective_user.id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start."""
    await update.message.reply_text(
        "Привет. Я Oleg_ML, бот для вопросов по Obsidian Vault.\n\n"
        "Команды:\n"
        "/auth пароль — получить доступ\n"
        "/whoami — узнать свой Telegram ID\n"
        "/logout — выйти\n"
        "/help — помощь"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help."""
    await update.message.reply_text(
        "Задай вопрос обычным сообщением. Я отправлю его в Flowise и верну ответ из заметок.\n"
        "Если доступа нет, используй /auth пароль."
    )


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает Telegram ID пользователя."""
    await update.message.reply_text(f"Твой Telegram ID: {get_user_id(update)}")


async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Авторизация по паролю."""
    user_id = get_user_id(update)

    if not context.args:
        await update.message.reply_text("Использование: /auth пароль")
        return

    password = " ".join(context.args)
    if authorize_by_password(user_id, password):
        await update.message.reply_text("Доступ выдан.")
    else:
        await update.message.reply_text("Неверный пароль.")


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет локальную авторизацию."""
    logout_user(get_user_id(update))
    await update.message.reply_text("Локальная авторизация удалена.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает обычные текстовые вопросы."""
    user_id = get_user_id(update)
    question = update.message.text.strip()

    logger.info("User %s question: %s", user_id, question)

    if not is_allowed(user_id):
        await update.message.reply_text(
            "Нет доступа. Используй /auth пароль или попроси добавить твой Telegram ID в allowlist."
        )
        return

    session_id = f"telegram_{user_id}"

    try:
        await update.message.chat.send_action(action=ChatAction.TYPING)
    except TimedOut:
        logger.warning("Telegram typing action timed out")

    try:
        result = await ask_flowise(question, session_id=session_id)
        message = format_answer(result["answer"], result["sources"])
        await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except httpx.ReadTimeout:
        logger.warning("Flowise response timed out")
        await update.message.reply_text("Flowise долго отвечает. Попробуй повторить вопрос чуть позже.")
    except Exception as error:
        logger.exception("Flowise request failed")
        await update.message.reply_text(f"Ошибка при обращении к Flowise: {error}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует ошибки Telegram, чтобы бот не падал молча."""
    if isinstance(context.error, TelegramError):
        logger.warning("Telegram error: %s", context.error)
    else:
        logger.exception("Unexpected error", exc_info=context.error)


def main() -> None:
    """Запускает Telegram-бота."""
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не задан")

    if not FLOWISE_URL or not FLOWISE_CHATFLOW_ID:
        raise RuntimeError("FLOWISE_URL или FLOWISE_CHATFLOW_ID не задан")

    builder = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
    )

    if TELEGRAM_PROXY_URL:
        builder = builder.proxy(TELEGRAM_PROXY_URL).get_updates_proxy(TELEGRAM_PROXY_URL)

    application = builder.build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("whoami", whoami))
    application.add_handler(CommandHandler("auth", auth))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Oleg_ML bot started")
    application.run_polling()


if __name__ == "__main__":
    main()
