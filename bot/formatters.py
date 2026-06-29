from html import escape


MAX_TELEGRAM_MESSAGE_LENGTH = 3900


def format_answer(answer: str, sources: list[str]) -> str:
    """Форматирует ответ для Telegram HTML parse mode."""
    text = escape(answer)

    if sources:
        source_lines = "\n".join(f"• <code>{escape(source)}</code>" for source in sources)
        text += f"\n\n<b>Источники:</b>\n{source_lines}"

    if len(text) > MAX_TELEGRAM_MESSAGE_LENGTH:
        text = text[:MAX_TELEGRAM_MESSAGE_LENGTH] + "\n\n..."

    return text
