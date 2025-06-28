import os
import logging
import re
from datetime import datetime

from telebot import types
from permissions import boss_only, admin_only
from config import bot, BOSS, PHOTOS, RULES_FILE, HELP_FILE, INVITE, MAGIC_CHAT_ID, BARTENDER
from polls import create_poll, unpin_poll
from utils import generate_report, clear_poll_results, clear_poll_id, load_yes_votes, set_friends, remove_friends
from buttons import send_reservation_buttons
from state import user_states
from events import create_event_poll, get_events_keyboard, get_confirmation_keyboard, delete_event, send_event_cancellation_notification, unpin_event_poll, get_events_list, get_events_keyboard_for_friends, add_event_friends, remove_event_friends


# Логирование
logger = logging.getLogger(__name__)

# Обработка команды /help
def help_command(message):
    logger.info(f"Текущая директория: {os.getcwd()}")
    try:
        with open(HELP_FILE, 'r', encoding='utf-8') as t:
            help_text = t.read()
        bot.send_message(message.chat.id, help_text)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла правил: {e}")


# Обработка команды /invite
def invite_link(message):
    bot.send_message(message.chat.id, f'Ссылка приглашение:\n {INVITE}')


# Обработка команды /rules
def beer_rules(message):
    media = []
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Пути к фотографиям: {PHOTOS}")
    
    # Обработка фотографий
    for path in PHOTOS:
        logger.info(f"Пытаемся открыть файл: {path}")
        if not os.path.exists(path):
            logger.error(f"Файл не существует: {path}")
            continue
        try:
            with open(path, 'rb') as photos:
                media.append(types.InputMediaPhoto(photos.read()))
        except Exception as e:
            logger.error(f"Ошибка при открытии файла {path}: {e}")
            continue
        
    # Обработка медиагруппы
    if media:
        bot.send_message(message.chat.id, "Ща всё узнаешь.")
        try:
            bot.send_media_group(message.chat.id, media)
        except Exception as e:
            logger.error(f"Ошибка при отправке медиагруппы: {e}")
            bot.send_message(ADMIN, "Произошла ошибка при отправке изображений")
    
    # Обработка текста правил
    try:
        with open(RULES_FILE, 'r', encoding='utf-8') as t:
            rules_text = t.read()
        bot.send_message(message.chat.id, rules_text)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла правил: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при чтении правил")


def plus_friends(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    yes_voters = [u['id'] for u in load_yes_votes()]
    
    if user_id not in yes_voters:
        bot.send_message(chat_id, "Ты не голосовал 'Да', поэтому не можешь привести друзей 🍺")
        return

    user_states[(user_id, chat_id)] = {"state": "waiting_friends", "type": "plus"}
    bot.send_message(chat_id, "Сколько друзей придет с тобой? Введи число.")


def minus_friends(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_states[(user_id, chat_id)] = {"state": "waiting_friends", "type": "minus"}
    bot.send_message(chat_id, "На сколько друзей меньше? Введи число.")

# Обработка нового участника
def greet_new_members(message):
    chat_id = message.chat.id
    for new_user in message.new_chat_members:
        user_id = new_user.id
        try:
            bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Да", callback_data=f"beer_yes_{user_id}"),
                types.InlineKeyboardButton("Нет", callback_data=f"beer_no_{user_id}")
            )
            bot.send_message(
                chat_id,
                f"Привет, {new_user.first_name}! Ты любишь пиво?",
                reply_markup=markup
            )
        except Exception as e:
            print(f"Ошибка при ограничении прав нового участника {user_id}: {e}")


# Обработка триггеров на текст:
def info(message):
    print(f"INFO: chat_id={message.chat.id}, user_id={message.from_user.id}, text={message.text}")

    # Вежливость в первую очередь.
    if 'привет' in message.text.lower():
        bot.send_message(message.chat.id, f'Ну привет, {message.from_user.first_name} {message.from_user.last_name or ""}..')

    # NO CEDH
    # CEDH CLUB
    elif (("cedh" in message.text.lower()
          or "cdh" in message.text.lower()
          or "сedh" in message.text.lower()
          or "сеdh" in message.text.lower()
          or "cеdh" in message.text.lower()
          or "сидиэйч" in message.text.lower()
          or "сиидиэйч" in message.text.lower()
          or "цедх" in message.text.lower()
          or "цeдх" in message.text.lower()
          or "цедx" in message.text.lower()
          or "цeдx" in message.text.lower()
          or "цдх" in message.text.lower()
          or "компот" in message.text.lower()
          or "компетитив" in message.text.lower())):
        bot.reply_to(message, "Ни слова про CEDH в этом чате!")

    # Glory to Bot
    elif (("бот крутой" in message.text.lower()
          or "крутой бот" in message.text.lower()
          or "классный бот" in message.text.lower()
          or "бот классный" in message.text.lower())
          or "хороший бот" in message.text.lower()
          or "бот хороший" in message.text.lower()):
        bot.reply_to(message, "Спасибо, бро! Обнял, поцеловал (не по-гейски)!")

    # Стас Special
    elif "стас" in message.text.lower():
        bot.reply_to(message, f"Блинб, Стас.... 🤤 ")
        
    # Friends
    key = (message.from_user.id, message.chat.id)
    if key in user_states:
        state = user_states[key]
        
        # Обработка состояний для друзей
        if state["state"] == "waiting_friends":
            try:
                count = int(message.text.strip())
            except ValueError:
                bot.send_message(message.chat.id, "Укажи ЧИСЛО, Дружище!")
                return

            if state["type"] == "plus":
                if count <= 0:
                    bot.send_message(message.chat.id, "У тебя чё друзья в отрицательных и нейтральных числах измеряются, умник?")
                    return
                set_friends(message.from_user, count)
                bot.send_message(message.chat.id, f"Отлично! Зафиксировал тебе {count} корешей.\nКоличество гедонистов-лудоманов неумолимо растет!\nТак держать!")

            elif state["type"] == "minus":
                from utils import load_friends, save_friends

                friends = load_friends()
                for f in friends:
                    if f['id'] == message.from_user.id:
                        f['count'] -= count
                        if f['count'] <= 0:
                            remove_friends(message.from_user)
                            bot.send_message(message.chat.id, "У тебя больше нет друзей.")
                        else:
                            save_friends(friends)
                            bot.send_message(message.chat.id, f"Окей, теперь с тобой придет {f['count']} друг(-а)")
                        break
                else:
                    bot.send_message(message.chat.id, "Ты ещё не добавлял друзей.")
            
            user_states.pop(key, None)
            return
            
        # Обработка состояний для создания событий
        elif state["state"] == "waiting_event_title":
            title = message.text.strip()
            if len(title) < 3:
                bot.send_message(message.chat.id, "Название должно содержать минимум 3 символа. Попробуйте еще раз:")
                return
                
            user_states[key] = {"state": "waiting_event_date", "title": title}
            bot.send_message(message.chat.id, "Введите дату в формате ДД.ММ.ГГГГ:")
            return
            
        elif state["state"] == "waiting_event_date":
            date_text = message.text.strip()
            # Проверяем формат даты
            if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_text):
                bot.send_message(message.chat.id, "Неверный формат даты. Используйте формат ДД.ММ.ГГГГ:")
                return
                
            try:
                event_date = datetime.strptime(date_text, '%d.%m.%Y')
                today = datetime.now()
                
                # Проверяем, что дата в будущем
                if event_date.date() <= today.date():
                    bot.send_message(message.chat.id, "Дата должна быть в будущем. Введите дату в формате ДД.ММ.ГГГГ:")
                    return
                    
            except ValueError:
                bot.send_message(message.chat.id, "Неверная дата. Введите дату в формате ДД.ММ.ГГГГ:")
                return
                
            title = state.get("title", "")
            user_states[key] = {"state": "waiting_event_time", "title": title, "date": date_text}
            bot.send_message(message.chat.id, "Введите время в формате ЧЧ:ММ:")
            return
            
        elif state["state"] == "waiting_event_time":
            time_text = message.text.strip()
            # Проверяем формат времени
            if not re.match(r'^\d{2}:\d{2}$', time_text):
                bot.send_message(message.chat.id, "Неверный формат времени. Используйте формат ЧЧ:ММ:")
                return
                
            try:
                event_time = datetime.strptime(time_text, '%H:%M')
                # Проверяем, что время в разумных пределах
                if event_time.hour < 8 or event_time.hour > 23:
                    bot.send_message(message.chat.id, "Время должно быть между 08:00 и 23:00. Введите время в формате ЧЧ:ММ:")
                    return
                    
            except ValueError:
                bot.send_message(message.chat.id, "Неверное время. Введите время в формате ЧЧ:ММ:")
                return
                
            title = state.get("title", "")
            date = state.get("date", "")
            
            # Создаем событие
            event_id, poll_message_id = create_event_poll(title, date, time_text)
            
            if event_id and poll_message_id:
                bot.send_message(message.chat.id, f"✅ Событие '{title}' создано на {date} в {time_text}!")
            else:
                bot.send_message(message.chat.id, "❌ Ошибка при создании события. Попробуйте еще раз.")
            
            user_states.pop(key, None)
            return
            
        # Обработка состояний для друзей событий
        elif state["state"] == "waiting_event_friends":
            try:
                count = int(message.text.strip())
            except ValueError:
                bot.send_message(message.chat.id, "Укажи ЧИСЛО, Дружище!")
                return

            event_id = state.get("event_id")
            if not event_id:
                bot.send_message(message.chat.id, "Ошибка: не выбрано событие. Попробуйте еще раз.")
                user_states.pop(key, None)
                return

            if state["type"] == "plus":
                if count <= 0:
                    bot.send_message(message.chat.id, "У тебя чё друзья в отрицательных и нейтральных числах измеряются, умник?")
                    return
                    
                success, message_text = add_event_friends(event_id, message.from_user, count)
                bot.send_message(message.chat.id, message_text)

            elif state["type"] == "minus":
                success, message_text = remove_event_friends(event_id, message.from_user, count)
                bot.send_message(message.chat.id, message_text)
            
            user_states.pop(key, None)
            return

        # Обработка состояний для команды shout
        elif state["state"] == "waiting_shout_text":
            shout_text = message.text.strip()
            
            if len(shout_text) < 5:
                bot.send_message(message.chat.id, "Текст анонса должен содержать минимум 5 символов. Попробуйте еще раз:")
                return
            
            try:
                # Отправляем анонс в групповой чат
                bot.send_message(MAGIC_CHAT_ID, shout_text)
                bot.send_message(ADMIN, "✅ Анонс успешно отправлен в групповой чат!")
                logger.info(f"Администратор {message.from_user.first_name} отправил анонс: {shout_text[:50]}...")
            except Exception as e:
                bot.send_message(ADMIN, "❌ Ошибка при отправке анонса. Попробуйте еще раз.")
                logger.error(f"Ошибка при отправке анонса: {e}")
            
            user_states.pop(key, None)
            return


# ============================== КОМАНДЫ РУЧНОГО ЗАПУСКА ==============================

# Обработка команды /pollnow
@boss_only
def manual_poll(message):
    """СОЗДАТЬ ОПРОС ВРУЧНУЮ"""
    create_poll(bot)
    bot.send_message(BOSS, "Опрос запущен вручную.")


# Обработка команды /events
def events_command(message):
    """ПОКАЗАТЬ СПИСОК НЕРЕГУЛЯРНЫХ МЕРОПРИЯТИЙ"""
    events_list = get_events_list()
    bot.send_message(message.chat.id, events_list)


# Обработка команды /addevent
@boss_only
def add_event_command(message):
    """СОЗДАТЬ НЕРЕГУЛЯРНОЕ МЕРОПРИЯТИЕ"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    user_states[(user_id, chat_id)] = {"state": "waiting_event_title"}
    bot.send_message(chat_id, "Введите название мероприятия:")


# Обработка команды /deleteevent
@boss_only
def delete_event_command(message):
    """УДАЛИТЬ НЕРЕГУЛЯРНОЕ МЕРОПРИЯТИЕ"""
    keyboard = get_events_keyboard()
    
    if not keyboard:
        bot.send_message(message.chat.id, "Нет активных нерегулярных мероприятий для удаления.")
        return
    
    bot.send_message(
        message.chat.id,
        "Выберите мероприятие для удаления:",
        reply_markup=keyboard
    )


# Обработка команды /pollres
@boss_only
def manual_poll_results(message):
    """ОТПРАВИТЬ РЕЗУЛЬТАТЫ ВРУЧНУЮ"""
    report, tables = generate_report()
    unpin_poll(bot)

    if report is None or tables == 0:
        # Никто не проголосовал "Да"
        bot.send_message(BOSS, "Нет данных для подсчета результатов.")
        try:
            bot.send_message(MAGIC_CHAT_ID, "Реки пива на этой неделе останутся нетронутыми..")
            bot.send_message(BARTENDER, "Привет, сегодня без брони. У магов неделя трезвости.")
        except Exception as e:
            print(f"Ошибка при отправке 'не придем' бармену: {e}")
        clear_poll_results()
        clear_poll_id()
        return

    try:
        bot.send_message(BOSS, "Голосование завершено вручную.")
        bot.send_message(BOSS, report)
        send_reservation_buttons(BOSS)
        bot.send_message(
            MAGIC_CHAT_ID,
            "Голосование завершено.\nВсем проголосовавшим летит плотная респектуля.\nРезультаты опроса отправлены Боссу."
        )
    except Exception as e:
        print(f"Ошибка при отправке результатов Боссу: {e}")
        try:
            bot.send_message(BOSS, "Ошибка при отправке результатов, Босс.")
        except:
            pass

# Обработка команды /gameon
@boss_only
def manual_gameon(message):
    """ПОЖЕЛАТЬ ХОРОШЕЙ ИГРЫ ВРУЧНУЮ"""
    bot.send_message(MAGIC_CHAT_ID, "Хорошей игры, господа маги!\nПусть победит хоть кто-нибудь, а напьется пива сильнейший!")


def plus_event_friends(message):
    """ДОБАВИТЬ ДРУЗЕЙ НА НЕРЕГУЛЯРНОЕ МЕРОПРИЯТИЕ"""
    keyboard = get_events_keyboard_for_friends()
    
    if not keyboard:
        bot.send_message(message.chat.id, "Нет активных нерегулярных мероприятий.")
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    user_states[(user_id, chat_id)] = {"state": "waiting_event_friends", "type": "plus"}
    
    bot.send_message(
        message.chat.id,
        "Выберите мероприятие для добавления друзей:",
        reply_markup=keyboard
    )


def minus_event_friends(message):
    """УБРАТЬ ДРУЗЕЙ С НЕРЕГУЛЯРНОГО МЕРОПРИЯТИЯ"""
    keyboard = get_events_keyboard_for_friends()
    
    if not keyboard:
        bot.send_message(message.chat.id, "Нет активных нерегулярных мероприятий.")
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    user_states[(user_id, chat_id)] = {"state": "waiting_event_friends", "type": "minus"}
    
    bot.send_message(
        message.chat.id,
        "Выберите мероприятие для удаления друзей:",
        reply_markup=keyboard
    )


# Обработка команды /shout
@admin_only
def shout_command(message):
    """ОТПРАВИТЬ АНОНС ОТ ИМЕНИ БОТА"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверяем, что команда вызвана в личном чате
    if message.chat.type != 'private':
        bot.send_message(chat_id, "Команда /shout доступна только в личном чате с ботом.")
        return
    
    user_states[(user_id, chat_id)] = {"state": "waiting_shout_text"}
    bot.send_message(ADMIN, "Введите текст анонса, который будет отправлен в групповой чат:")








