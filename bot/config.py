import os
import logging
from telebot import TeleBot
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

logger = logging.getLogger(__name__)

def get_project_root():
    """Возвращает абсолютный путь к корню проекта."""
    current_file = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(current_file))

PROJECT_ROOT = get_project_root()

# FILES:
RULES_FILE = os.path.join(PROJECT_ROOT, 'text', 'rules.txt')
HELP_FILE = os.path.join(PROJECT_ROOT, 'text', 'help.txt')
PHOTOS = [
    os.path.join(PROJECT_ROOT, 'img', 'brackets.jpeg'),
    os.path.join(PROJECT_ROOT, 'img', 'changers.jpeg')
]

# Проверяем существование файлов при импорте
for photo in PHOTOS:
    if not os.path.exists(photo):
        logger.error(f"Файл не существует: {photo}")
        # Картинок не существует
    else:
        logger.info(f"Файл существует: {photo}")

if not os.path.exists(RULES_FILE):
    logger.error(f"Файл с правилами не существует: {RULES_FILE}")
    # Текста правил не существует
else:
    logger.info(f"Файл с правилами существует: {RULES_FILE}")

# MAIN INFO:
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Не задан токен бота (TOKEN) в .env файле")

MAGIC_CHAT_ID = os.getenv("MAGIC_CHAT_ID")
if not MAGIC_CHAT_ID:
    raise ValueError("Не задан MAGIC_CHAT_ID в .env файле")
MAGIC_CHAT_ID = int(MAGIC_CHAT_ID)

# ADDITIONAL INFO
INVITE = os.getenv("INVITE")

# PERSONS:
BOSS = int(os.getenv("BOSS"))
STAS = int(os.getenv("STAS"))
SIMON = int(os.getenv("SIMON"))
BOSSES = [BOSS, STAS, SIMON]

BARTENDER = int(os.getenv("BARTENDER"))

# BOT:
bot = TeleBot(TOKEN)

# DATA:
POLL_DATA_FILE = "poll_id.json"
POLL_RESULTS = "votes.json"
