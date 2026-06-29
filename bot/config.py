import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUTHORIZED_USERS_FILE = DATA_DIR / "authorized_users.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "")

FLOWISE_URL = os.getenv("FLOWISE_URL", "http://localhost:3000").rstrip("/")
FLOWISE_CHATFLOW_ID = os.getenv("FLOWISE_CHATFLOW_ID", "")
FLOWISE_API_KEY = os.getenv("FLOWISE_API_KEY", "")

BOT_ACCESS_PASSWORD = os.getenv("BOT_ACCESS_PASSWORD", "")
ALLOWED_TELEGRAM_USER_IDS = {
    int(user_id.strip())
    for user_id in os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").split(",")
    if user_id.strip().isdigit()
}

REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "180"))
