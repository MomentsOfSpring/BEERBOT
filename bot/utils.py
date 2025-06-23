import json
import logging
from datetime import datetime, timedelta

from config import POLL_DATA_FILE, POLL_RESULTS, FRIENDS_FILE, MAGIC_CHAT_ID


logger = logging.getLogger(__name__)


# Сохранение опроса:
def save_poll(message_id, poll_id):
    try:
        with open(POLL_DATA_FILE, 'w') as f:
            json.dump({
                "message_id": message_id,
                "poll_id": poll_id
            }, f)
        logger.info(f"ID опроса сохранён: message_id={message_id}, poll_id={poll_id}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении опроса: {e}")


# Загрузка опроса, чтобы потом открепить:
def load_poll():
    try:
        with open(POLL_DATA_FILE, 'r') as f:
            data = json.load(f)
        
        message_id = data.get("message_id")
        poll_id = data.get("poll_id")

        if not message_id or not poll_id:
            logger.warning("Файл опроса не содержит message_id или poll_id.")
            return None, None, None
            
        logger.info(f"Опрос загружен: chat_id={MAGIC_CHAT_ID}, message_id={message_id}, poll_id={poll_id}")
        return MAGIC_CHAT_ID, message_id, poll_id

    except FileNotFoundError:
        logger.warning("Файл с ID опроса не найден.")
        return None, None, None
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON в файле опроса.")
        return None, None, None


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


# Удаление голоса "Да":
def remove_yes_vote(user_id):
    try:
        results = load_yes_votes()
        # Фильтруем список, оставляя только тех пользователей, чей ID не совпадает с указанным
        updated_results = [vote for vote in results if vote["id"] != user_id]
        
        # Сохраняем обновленный список
        with open(POLL_RESULTS, 'w') as f:
            json.dump(updated_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Удален голос пользователя с ID: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении голоса: {e}")
        return False


# Функция создания опроса:
def generate_report():
    voters = load_yes_votes()
    friends = load_friends()

    if not voters:
        return None, 0  # <- теперь возвращаем кортеж (None, 0)

    total = len(voters) + sum(f["count"] for f in friends)
    tables = (total + 3) // 4  # округление вверх, 4 человека за стол

    report_lines = [
        "Любители пива на этой неделе:",
        f"Всего участников: {total}",
        f"Рекомендуемое количество столов: {tables}",
        "",
        "Список:"
    ]

    for i, user in enumerate(voters, 1):
        line = f"{i}. {user['first_name']} {user['last_name']}".strip()
        for f in friends:
            if f["id"] == user["id"]:
                line += f" +{f['count']} друг(-а)"
                break
        line += f" (id: {user['id']})"
        report_lines.append(line)

    return "\n".join(report_lines), tables  # <- возвращаем кортеж


def clear_poll_results():
    """Очищает файл с результатами голосования (votes.json)."""
    try:
        with open(POLL_RESULTS, 'w') as f:
            json.dump([], f)
        logger.info("Результаты опроса очищены.")
        with open(FRIENDS_FILE, 'w') as f:
            f.write('[]')
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


# Загрузка друзей
def load_friends():
    try:
        with open(FRIENDS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Сохранение
def save_friends(data):
    with open(FRIENDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Добавление или обновление
def set_friends(user, count):
    friends = load_friends()
    for f in friends:
        if f['id'] == user.id:
            f['count'] = count
            save_friends(friends)
            return
    friends.append({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name or "",
        "count": count
    })
    save_friends(friends)


# Удаление если ноль
def remove_friends(user):
    friends = load_friends()
    friends = [f for f in friends if f['id'] != user.id]
    save_friends(friends)