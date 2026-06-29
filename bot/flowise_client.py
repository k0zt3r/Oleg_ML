import httpx

from bot.config import FLOWISE_API_KEY, FLOWISE_CHATFLOW_ID, FLOWISE_URL, REQUEST_TIMEOUT


def extract_answer(data: dict) -> str:
    """Достает ответ из разных форматов Flowise."""
    nested = data.get("data") or {}

    answer = (
        nested.get("text")
        or nested.get("answer")
        or data.get("text")
        or data.get("answer")
        or data.get("response")
    )

    return answer or "Flowise вернул пустой ответ."


def extract_sources(data: dict) -> list[str]:
    """Пробует достать источники из ответа Flowise."""
    sources = data.get("sourceDocuments") or data.get("sources") or []
    result = []

    for source in sources[:5]:
        metadata = source.get("metadata", {}) if isinstance(source, dict) else {}
        source_name = metadata.get("source") or metadata.get("file_path") or metadata.get("loc")
        if source_name:
            result.append(str(source_name))

    return result


async def ask_flowise(question: str, session_id: str) -> dict:
    """Отправляет вопрос в Flowise Prediction API."""
    endpoint = f"{FLOWISE_URL}/api/v1/prediction/{FLOWISE_CHATFLOW_ID}"

    payload = {
        "question": question,
        "overrideConfig": {
            "sessionId": session_id,
        },
    }

    headers = {"Content-Type": "application/json"}
    if FLOWISE_API_KEY:
        headers["Authorization"] = f"Bearer {FLOWISE_API_KEY}"
        headers["x-api-key"] = FLOWISE_API_KEY

    timeout = httpx.Timeout(REQUEST_TIMEOUT, connect=20)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    return {
        "answer": extract_answer(data),
        "sources": extract_sources(data),
        "raw": data,
    }
