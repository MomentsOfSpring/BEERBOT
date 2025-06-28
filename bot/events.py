import json
import logging
import os
from datetime import datetime, timedelta
from telebot import types
from config import bot, MAGIC_CHAT_ID, BARTENDER, BOSSES
from utils import load_yes_votes, load_friends

logger = logging.getLogger(__name__)

# Файл для хранения всех событий
EVENTS_FILE = "events.json"
# Директория для хранения данных событий
EVENTS_DATA_DIR = "events_data"

# Создаем директорию для данных событий, если её нет
if not os.path.exists(EVENTS_DATA_DIR):
    os.makedirs(EVENTS_DATA_DIR)


def save_event(event_data):
    """Сохраняет событие в основной файл событий"""
    try:
        events = load_all_events()
        events.append(event_data)
        
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Событие сохранено: {event_data['title']} на {event_data['date']}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении события: {e}")
        return False


def load_all_events():
    """Загружает все события из файла"""
    try:
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_event_data(event_id, data):
    """Сохраняет данные участников для конкретного события"""
    try:
        filename = os.path.join(EVENTS_DATA_DIR, f"sideevent_{event_id}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Данные события {event_id} сохранены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных события {event_id}: {e}")
        return False


def load_event_data(event_id):
    """Загружает данные участников для конкретного события"""
    try:
        filename = os.path.join(EVENTS_DATA_DIR, f"sideevent_{event_id}.json")
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"participants": [], "friends": []}


def delete_event(event_id):
    """Удаляет событие и его данные"""
    try:
        # Удаляем из основного списка событий
        events = load_all_events()
        events = [e for e in events if e['id'] != event_id]
        
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        
        # Удаляем файл с данными события
        filename = os.path.join(EVENTS_DATA_DIR, f"sideevent_{event_id}.json")
        if os.path.exists(filename):
            os.remove(filename)
        
        logger.info(f"Событие {event_id} удалено")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении события {event_id}: {e}")
        return False


def get_event_by_id(event_id):
    """Получает событие по ID"""
    events = load_all_events()
    for event in events:
        if event['id'] == event_id:
            return event
    return None


def create_event_poll(title, date, time):
    """Создает опрос для нерегулярного мероприятия"""
    try:
        # Создаем уникальный ID для события
        event_id = f"{date.replace('.', '')}_{int(datetime.now().timestamp())}"
        
        # Создаем опрос
        poll_message = bot.send_poll(
            MAGIC_CHAT_ID,
            question=f"{title}, {date}, {time}",
            options=["Да", "Нет"],
            is_anonymous=False,
            allows_multiple_answers=False
        )
        
        # Сохраняем событие
        event_data = {
            "id": event_id,
            "title": title,
            "date": date,
            "time": time,
            "poll_message_id": poll_message.message_id,
            "poll_id": poll_message.poll.id,
            "created_at": datetime.now().isoformat()
        }
        
        if save_event(event_data):
            # Закрепляем опрос
            bot.pin_chat_message(
                MAGIC_CHAT_ID,
                poll_message.message_id,
                disable_notification=True
            )
            
            # Инициализируем пустые данные события
            save_event_data(event_id, {"participants": [], "friends": []})
            
            logger.info(f"Создан опрос для события: {title} на {date} {time}")
            return event_id, poll_message.message_id
        
        return None, None
        
    except Exception as e:
        logger.error(f"Ошибка при создании опроса события: {e}")
        return None, None


def handle_event_poll_answer(poll_answer):
    """Обработчик ответов в опросе события"""
    try:
        # Находим событие по poll_id
        events = load_all_events()
        event = None
        for e in events:
            if e.get('poll_id') == poll_answer.poll_id:
                event = e
                break
        
        if not event:
            logger.warning(f"Событие с poll_id {poll_answer.poll_id} не найдено")
            return
        
        event_id = event['id']
        event_data = load_event_data(event_id)
        
        user = poll_answer.user
        user_info = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name or ""
        }
        
        # Если пользователь выбрал "Да" (option_id = 0)
        if 0 in poll_answer.option_ids:
            # Проверяем, не голосовал ли уже
            if user.id not in [p['id'] for p in event_data['participants']]:
                event_data['participants'].append(user_info)
                save_event_data(event_id, event_data)
                logger.info(f"Добавлен участник {user.first_name} в событие {event['title']}")
        # Если пользователь выбрал "Нет" или отменил голос
        else:
            # Удаляем из участников
            event_data['participants'] = [p for p in event_data['participants'] if p['id'] != user.id]
            save_event_data(event_id, event_data)
            logger.info(f"Удален участник {user.first_name} из события {event['title']}")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке голоса в событии: {e}")


def send_event_notification(event_id):
    """Отправляет уведомление бармену о событии"""
    try:
        event = get_event_by_id(event_id)
        if not event:
            logger.error(f"Событие {event_id} не найдено")
            return
        
        event_data = load_event_data(event_id)
        participants_count = len(event_data['participants'])
        friends_count = sum(f['count'] for f in event_data.get('friends', []))
        total_count = participants_count + friends_count
        
        # Рассчитываем количество столов (4 человека за стол)
        tables = (total_count + 3) // 4
        
        message = f"Привет! Сегодня маги решили нерегулярно собраться!\nВот столько человек придёт: {total_count} (участников: {participants_count}, друзей: {friends_count}), нужно {tables} столов."
        
        bot.send_message(BARTENDER, message)
        logger.info(f"Отправлено уведомление бармену о событии {event['title']}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о событии: {e}")


def send_event_confirmation(event_id):
    """Отправляет подтверждение о бронировании"""
    try:
        event = get_event_by_id(event_id)
        if not event:
            logger.error(f"Событие {event_id} не найдено")
            return
        
        message = f"Я забронировал кабак на {event['title']}. Теперь можете напиться пива и отшлепать друг друга карточками. Не благодарите.."
        
        bot.send_message(MAGIC_CHAT_ID, message)
        logger.info(f"Отправлено подтверждение о событии {event['title']}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке подтверждения события: {e}")


def unpin_event_poll(event_id):
    """Открепляет опрос события"""
    try:
        event = get_event_by_id(event_id)
        if not event:
            logger.error(f"Событие {event_id} не найдено")
            return False
        
        poll_message_id = event.get('poll_message_id')
        if not poll_message_id:
            logger.error(f"ID сообщения опроса не найден для события {event_id}")
            return False
        
        bot.unpin_chat_message(
            chat_id=MAGIC_CHAT_ID,
            message_id=poll_message_id
        )
        
        logger.info(f"Опрос события {event['title']} откреплен")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при откреплении опроса события: {e}")
        return False


def get_events_keyboard():
    """Создает клавиатуру с датами событий для удаления"""
    events = load_all_events()
    if not events:
        return None
    
    keyboard = types.InlineKeyboardMarkup()
    
    for event in events:
        button_text = f"{event['title']} - {event['date']} {event['time']}"
        callback_data = f"delete_event_{event['id']}"
        keyboard.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    return keyboard


def get_confirmation_keyboard(event_id):
    """Создает клавиатуру подтверждения удаления"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Точно, удалить", callback_data=f"confirm_delete_{event_id}"),
        types.InlineKeyboardButton("Я передумал", callback_data="cancel_delete")
    )
    return keyboard


def send_event_cancellation_notification(event_id):
    """Отправляет уведомление об отмене события"""
    try:
        event = get_event_by_id(event_id)
        if not event:
            logger.error(f"Событие {event_id} не найдено")
            return
        
        message = f"Босс решил отменить ивент {event['title']} на {event['date']} {event['time']}"
        
        bot.send_message(MAGIC_CHAT_ID, message)
        logger.info(f"Отправлено уведомление об отмене события {event['title']}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об отмене события: {e}")


def get_events_list():
    """Возвращает список активных событий в читаемом формате"""
    events = load_all_events()
    
    if not events:
        return "Нерегулярные ивенты пока не запланированы"
    
    # Сортируем события по дате
    events.sort(key=lambda x: datetime.strptime(x['date'], '%d.%m.%Y'))
    
    events_list = []
    for event in events:
        events_list.append(f"{event['title']} - {event['date']}")
    
    return "\n".join(events_list)


def schedule_event_notifications():
    """Планирует уведомления для всех предстоящих событий"""
    try:
        events = load_all_events()
        today = datetime.now().date()
        
        for event in events:
            try:
                event_date = datetime.strptime(event['date'], '%d.%m.%Y').date()
                event_time = datetime.strptime(event['time'], '%H:%M').time()
                event_datetime = datetime.combine(event_date, event_time)
                
                # Если событие сегодня и через 4 часа
                if event_date == today:
                    now = datetime.now()
                    time_until_event = event_datetime - now
                    
                    # Если до события 4 часа или меньше
                    if timedelta(hours=3, minutes=55) <= time_until_event <= timedelta(hours=4, minutes=5):
                        send_event_notification(event['id'])
                        
                        # Отправляем подтверждение и открепляем опрос
                        send_event_confirmation(event['id'])
                        unpin_event_poll(event['id'])
                        
                        # Удаляем событие после обработки
                        delete_event(event['id'])
                        
            except Exception as e:
                logger.error(f"Ошибка при обработке события {event.get('title', 'Unknown')}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка при планировании уведомлений событий: {e}")


def get_events_keyboard_for_friends():
    """Создает клавиатуру с датами событий для добавления друзей"""
    events = load_all_events()
    if not events:
        return None
    
    keyboard = types.InlineKeyboardMarkup()
    
    for event in events:
        button_text = f"{event['title']} - {event['date']} {event['time']}"
        callback_data = f"event_friends_{event['id']}"
        keyboard.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    return keyboard


def add_event_friends(event_id, user, count):
    """Добавляет друзей к событию"""
    try:
        event_data = load_event_data(event_id)
        
        # Проверяем, есть ли уже пользователь в списке участников
        participants = event_data.get('participants', [])
        user_in_participants = any(p['id'] == user.id for p in participants)
        
        if not user_in_participants:
            return False, "Сначала нужно проголосовать 'Да' в опросе события"
        
        # Добавляем или обновляем друзей
        friends = event_data.get('friends', [])
        for friend in friends:
            if friend['id'] == user.id:
                friend['count'] += count
                save_event_data(event_id, event_data)
                return True, f"Добавлено {count} друзей. Всего с тобой придет {friend['count']} друг(-а)"
        
        # Если пользователя нет в списке друзей, добавляем
        friends.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name or "",
            "count": count
        })
        save_event_data(event_id, event_data)
        return True, f"Добавлено {count} друзей к событию"
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении друзей к событию {event_id}: {e}")
        return False, "Ошибка при добавлении друзей"


def remove_event_friends(event_id, user, count):
    """Убирает друзей от события"""
    try:
        event_data = load_event_data(event_id)
        friends = event_data.get('friends', [])
        
        for friend in friends:
            if friend['id'] == user.id:
                friend['count'] -= count
                if friend['count'] <= 0:
                    friends = [f for f in friends if f['id'] != user.id]
                    save_event_data(event_id, event_data)
                    return True, "У тебя больше нет друзей на этом событии"
                else:
                    save_event_data(event_id, event_data)
                    return True, f"Убрано {count} друзей. Теперь с тобой придет {friend['count']} друг(-а)"
        
        return False, "Ты ещё не добавлял друзей на это событие"
        
    except Exception as e:
        logger.error(f"Ошибка при удалении друзей от события {event_id}: {e}")
        return False, "Ошибка при удалении друзей" 