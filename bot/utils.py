import json
import logging
from datetime import datetime, timedelta

from config import POLL_DATA_FILE, POLL_RESULTS



logger = logging.getLogger(__name__)


# Сохранение опроса:
def save_poll(chat_id, message_id):
    try:
        with open(POLL_DATA_FILE, 'w') as f:
            json.dump({
                "chat_id": chat_id,
                "message_id": message_id
            }, f)
        logger.info(f"Опрос сохранён: chat_id={chat_id}, message_id={message_id}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении опроса: {e}")


# Загрузка опроса, чтобы потом открепить:
def load_poll():
    try:
        with open(POLL_DATA_FILE, 'r') as f:
            data = json.load(f)
            logger.info(f"Опрос загружен: chat_id={data['chat_id']}, message_id={data['message_id']}")
            return data["chat_id"], data["message_id"]
    except FileNotFoundError:
        logger.warning("Файл с ID опроса не найден.")
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Ошибка при чтении файла опроса: {e}")
    return None, None


# Сохранение любителей пива и карточек:
def save_yes_vote(user):
    try:
        with open(POLL_RESULTS, 'r') as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        results = []

    # Не сохраняем двойных любителей пива
    if user.id in [u["id"] for u in results]:
        return
    results.append({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name or ""
    })

    with open(POLL_RESULTS, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    full_name = f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    logger.info(f"Добавлен голос от {user.first_name} (@{user.username})")


# Загрузка проголосовавших "Да":
def load_yes_votes():
    try:
        with open(POLL_RESULTS, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Функция создания опроса:
def generate_report():
    voters = load_yes_votes()

    if not voters:
        return None, 0  # <- теперь возвращаем кортеж (None, 0)

    total = len(voters)
    tables = (total + 3) // 4  # округление вверх, 4 человека за стол

    report_lines = [
        "Любители пива на этой неделе:",
        f"Всего участников: {total}",
        f"Рекомендуемое количество столов: {tables}",
        "",
        "Список:"
    ]

    for i, user in enumerate(voters, 1):
        name = f"{user['first_name']} {user['last_name']}".strip()
        report_lines.append(f"{i}. {name} (id: {user['id']})")

    return "\n".join(report_lines), tables  # <- возвращаем кортеж


def clear_poll_results():
    """Очищает файл с результатами голосования (votes.json)."""
    try:
        with open(POLL_RESULTS, 'w') as f:
            json.dump([], f)
        logger.info("Результаты опроса очищены.")
    except Exception as e:
        logger.error(f"Ошибка при очистке результатов опроса: {e}")

def clear_poll_id():
    """Очищает файл с id опроса (poll_id.json)."""
    try:
        with open(POLL_DATA_FILE, 'w') as f:
            json.dump({}, f)
        logger.info("ID опроса очищен.")
    except Exception as e:
        logger.error(f"Ошибка при очистке ID опроса: {e}")

def get_next_wednesday():
    today = datetime.now()
    days_ahead = (2 - today.weekday()) % 7  # 2 = среда
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


