import os
import logging
import re
from datetime import datetime

from telebot import types
from permissions import boss_only, admin_only
from config import bot, BOSS, PHOTOS, RULES_FILE, HELP_FILE, INVITE, MAGIC_CHAT_ID, BARTENDER, ADMIN
from polls import create_poll, unpin_poll
from utils import generate_report, clear_poll_results, clear_poll_id, load_yes_votes, set_friends, remove_friends, load_friends, save_friends
from buttons import send_reservation_buttons
from state import user_states
from events import create_event_poll, get_events_keyboard, get_confirmation_keyboard, delete_event, send_event_cancellation_notification, unpin_event_poll, get_events_list, get_events_keyboard_for_friends, add_event_friends, remove_event_friends, load_all_events, load_event_data, get_event_by_id, save_event_data
from random import choice


# Логирование
logger = logging.getLogger(__name__)

def help_command(message):
    """Обработка команды /help - вызов текста помощи"""
    logger.info(f"Текущая директория: {os.getcwd()}")
    try:
        with open(HELP_FILE, 'r', encoding='utf-8') as t:
            help_text = t.read()
        bot.send_message(message.chat.id, help_text)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла правил: {e}")


def invite_link(message):
    """Обработка команды /invite - отправка ботом ссылки-приглашения в чат, откуда была вызвана"""
    bot.send_message(message.chat.id, f'Ссылка приглашение:\n {INVITE}')


def beer_rules(message):
    """Обработка команды /rules - отправка ботом текста правил в чат, откуда была вызвана"""
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
        bot.send_message(ADMIN, "Произошла ошибка при чтении правил")


def set_friends(message):
    """Функция команды /setfriends - добавление друзей на регулярное мероприятие"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    yes_voters = [u['id'] for u in load_yes_votes()]
    
    if user_id not in yes_voters:
        bot.send_message(chat_id, "Ты не голосовал 'Да', поэтому не можешь привести друзей 🍺")
        return

    user_states[(user_id, chat_id)] = {"state": "waiting_friends", "type": "set"}
    bot.send_message(chat_id, "Сколько друзей придет с тобой? Введи число.")


def minus_friends(message):
    """Функция команды /minus friends - удаление друзей с регулярного мероприятия"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_states[(user_id, chat_id)] = {"state": "waiting_friends", "type": "minus"}
    bot.send_message(chat_id, "На сколько друзей меньше? Введи число.")


def greet_new_members(message):
    """Функция-Триггер на появление нового участника чата"""
    chat_id = message.chat.id
    for new_user in message.new_chat_members:
        user_id = new_user.id
        try: # Ограничиваем ему доступ ко всему, пока ответит на вопрос про пиво.
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


def info(message):
    """Функция обработки триггеров на текст"""
    print(f"INFO: chat_id={message.chat.id}, user_id={message.from_user.id}, text={message.text}")

    # Приоритет на вежливость.
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
          or "кедх" in message.text.lower()
          or "кдх" in message.text.lower()
          or "компетитив" in message.text.lower())):
        phrases = ["Ни слова про CEDH в этом чате!", "Внимание! Обнаружена угроза CEDH!\nПарни, готовьте свои COUNETERSPELLS..", "Отставить cEDH!", "CringeDH..", "Агаааа, попался! Цедхшник.."]
        bot.reply_to(message, choice(phrases))
        
    # Format memes:
    elif (" стандарт " in message.text.lower()
          or "standard" in message.text.lower()):
        bot.reply_to(message, f"Стандарт мёртв, чуваки. 🤡")
    elif ("пионер" in message.text.lower()
          or "pioner" in message.text.lower()):
        bot.reply_to(message, "Уууу, пацаны, да у нас тут пионерщик..\nДырявим его!")
    elif ("премодерн" in message.text.lower()
          or "premodern" in message.text.lower()):
        bot.reply_to(message, "Отличный выдуманный формат, чтобы поиграть со своим парнем!")
    elif ("модерн" in message.text.lower()
          or "modern" in message.text.lower()):
        bot.reply_to(message, "Модерн для геев!")
    elif ("легаси" in message.text.lower()
          or "легоси" in message.text.lower()
          or "legacy" in message.text.lower()):
        bot.reply_to(message, "Хуегаси")
    elif ("паупер" in message.text.lower()
          or "пупер" in message.text.lower()
          or "pauper" in message.text.lower()):
        bot.reply_to(message, "паупер для бомжей бтв 🤡")
    elif ("винтаж" in message.text.lower()
          or "vintage" in message.text.lower()):
        bot.reply_to(message, "Какой тебе ещё винтаж? По йогурту и спать.")
    elif "elder dragon highlander" in message.text.lower():
        bot.reply_to(message, f"Эвона как ты завернул")
    elif ("edh" in message.text.lower()
          or "едх" in message.text.lower()):
        bot.reply_to(message, "Блинб, ЕДХ.... 🤤")
    elif ("эрмитаж" in message.text.lower()
          or "heritage" in message.text.lower()
          or "центурион" in message.text.lower()
          or "centurion" in message.text.lower()
          or "легаси куб" in message.text.lower()):
        bot.reply_to(message, "Опять выдуманный формат..\nПарни, звоните в дурку.")
    elif (" арена " in message.text.lower()
          or "арене" in message.text.lower()
          or "аренка" in message.text.lower()
          or "арену" in message.text.lower()
          or "аренке" in message.text.lower()
          or "аренку" in message.text.lower()):
        bot.reply_to(message, "ПАРНИ, АНЕКДОТ!\nПриходит игрок в арену домой и говорит своему парню 'Схлестнемся на мечах, Гладиатор?' 🤡")
    elif ("rudc" in message.text.lower()
          or "рудк" in message.text.lower()
          or "рудц" in message.text.lower()
          or "duel commander" in message.text.lower()
          or "рудх" in message.text.lower()):
        bot.reply_to(message, "Отличный выдуманный формат, чтобы поиграть со своим парнем!")
    elif ("дуэльник" in message.text.lower()
          or "дуэльный" in message.text.lower()):
        bot.reply_to(message, f"Дуэльная магия - это втихаря тапать друг друга 🤡")
    
    # Glory to Beer
    elif (" пиво " in message.text.lower()
          or " пива " in message.text.lower()):
        bot.reply_to(message, "Пиво в стеке! Ответы?")
        
    # Only LoveCraft
    elif ("игроментал" in message.text.lower()
          or "хоббигеймс" in message.text.lower()
          or "единорог" in message.text.lower()
          or " хг " in message.text.lower()
          or " роге " in message.text.lower()
          or " рога " in message.text.lower()):
        bot.reply_to(message, "ВНИМАНИЕ!\nВражеская реклама гейклуба!\nВсем приготовить свою гетеросексуальность!")

    # Стас Special
    elif "стас" in message.text.lower():
        bot.reply_to(message, f"Блинб, Стас.... 🤤 ")
    
    # Random memes
    elif " бот " in message.text.lower():
        bot.reply_to(message, f"Чё тебе надо?")
    elif "контра" in message.text.lower():
        bot.reply_to(message, f"Контра? В стек консиднул.")
    elif ("ристик" in message.text.lower()
          or "ремора" in message.text.lower()):
        bot.reply_to(message, "Доплачивать будешь?")
    elif ("юрико" in message.text.lower()
          or "yuriko" in message.text.lower()):
        bot.reply_to(message, "Юрико? Триггер!\nВ ебало всем на 15!")
    elif "легосеки" in message.text.lower():
        bot.reply_to(message, f"Легосеки - Гомосеки")
    elif "легосек" in message.text.lower():
        bot.reply_to(message, f"Легосек - Гомосек")
        
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

            # Установить количество друзей
            if state["type"] == "set":
                if count <= 0:
                    bot.send_message(message.chat.id, "У тебя чё друзья в отрицательных и нейтральных числах измеряются, умник?")
                    return
                set_friends(message.from_user, count)
                bot.send_message(message.chat.id, f"Отлично! Зафиксировал тебе {count} корешей.\nКоличество гедонистов-лудоманов неумолимо растет!\nТак держать!")

            # Уменьшить количество друзей
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
        
        # Установка даты на НЕРЕГУЛЯРНОЕ событие
        elif state["state"] == "waiting_event_date":
            date_text = message.text.strip()
            # Проверяем формат даты
            if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', date_text):
                bot.send_message(message.chat.id, "Неверный формат даты. Используйте формат ДД.ММ.ГГГГ:")
                return
                
            try:
                event_date = datetime.strptime(date_text, '%d.%m.%Y')
                today = datetime.now()
                
                # Проверяем, что дата в будущем, а то всякое бывает..
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
        
        # Установка времени на НЕРЕГУЛЯРНОЕ событие
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
            
            # Создаем НЕРЕГУЛЯРНОЕ событие
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

            # Пользователь выбирает ивент
            event_id = state.get("event_id")
            if not event_id:
                bot.send_message(message.chat.id, "Ошибка: не выбрано событие. Попробуйте еще раз.")
                user_states.pop(key, None)
                return

            # Пользователь указывает количество друзей
            if state["type"] == "set":
                if count <= 0:
                    bot.send_message(message.chat.id, "У тебя чё друзья в отрицательных и нейтральных числах измеряются, умник?")
                    return
                    
                success, message_text = add_event_friends(event_id, message.from_user, count)
                bot.send_message(message.chat.id, message_text)

            # Пользователь указывает количество друзей
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


@boss_only
def manual_poll(message):
    """Функция команды /pollnow - РУЧНОЕ создание опроса вручную"""
    create_poll(bot)
    bot.send_message(BOSS, "Опрос запущен вручную.")


@boss_only
def manual_poll_results(message):
    """Функция команды /pollres - РУЧНАЯ отправка результатов опроса Босссу на бронирование"""
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
        bot.send_message(MAGIC_CHAT_ID, report)
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
    """Функция команды /gameon - Ручная отправка пожеланий хорошей игры в групповой чат и удаление результатов опроса"""
    clear_poll_results()
    clear_poll_id()
    bot.send_message(MAGIC_CHAT_ID, "Хорошей игры, господа маги!\nПусть победит хоть кто-нибудь, а напьется пива сильнейший!")


# Обработка команды /shout
@admin_only
def shout_command(message):
    """Функция команды /shout - Отправление сообщений от лица бота"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверяем, что команда вызвана в личном чате
    if message.chat.type != 'private':
        bot.send_message(chat_id, "Команда /shout доступна только в личном чате с ботом.")
        return
    
    user_states[(user_id, chat_id)] = {"state": "waiting_shout_text"}
    bot.send_message(chat_id, "Введите текст анонса, который будет отправлен в групповой чат:")


def skolkobudetnaroda(message):
    """Функция команды /skolkobudetnaroda - Отправление ботом раннего отчета в чат"""
    try:
        report, tables = generate_report()
        
        # Проверяем, есть ли активный опрос и участники
        if report is None or tables == 0:
            bot.send_message(message.chat.id, "Рановато интересоваться, дружище..")
            return
        
        try:
            bot.send_message(message.chat.id, report)    
        except Exception as e:
            logger.error(f"Ошибка в /skolkobudetnaroda: {e}")
            bot.send_message(message.chat.id, "Рановато интересоваться, дружище..")
            bot.send_message(ADMIN, "Произошла ошибка при подсчёте народу.")
    except Exception as e:
            logger.error(f"Ошибка в /skolkobudetnaroda: {e}")
            bot.send_message(message.chat.id, "Рановато интересоваться, дружище..")
            bot.send_message(ADMIN, "Произошла ошибка при подсчёте народу.")


# ============================== КОМАНДЫ НЕРЕГУЛЯРНЫХ ИВЕНТОВ (BETA) ==============================


def events_command(message):
    """Функция команды /events - Вывод списка НЕРЕГУЛЯРНЫХ мероприятий"""
    events_list = get_events_list()
    bot.send_message(message.chat.id, events_list)


@boss_only
def add_event_command(message):
    """Функция команды /addevent - Создание НЕРЕГУЛЯРНОГО ивента"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    user_states[(user_id, chat_id)] = {"state": "waiting_event_title"}
    bot.send_message(chat_id, "Введите название мероприятия:")


@boss_only
def delete_event_command(message):
    """Функция команды /deleteevent - Удаление НЕРЕГУЛЯРНОГО ивента"""
    keyboard = get_events_keyboard()
    
    if not keyboard:
        bot.send_message(message.chat.id, "Нет активных нерегулярных мероприятий для удаления.")
        return
    
    bot.send_message(
        message.chat.id,
        "Выберите мероприятие для удаления:",
        reply_markup=keyboard
    )


def set_event_friends(message):
    """Функция команды /seteventfriends - Добавление друзей на НЕРЕГУЛЯРНЫЙ ивент"""
    keyboard = get_events_keyboard_for_friends()
    
    if not keyboard:
        bot.send_message(message.chat.id, "Нет активных нерегулярных мероприятий.")
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    user_states[(user_id, chat_id)] = {"state": "waiting_event_friends", "type": "set"}
    
    bot.send_message(
        message.chat.id,
        "Выберите мероприятие для добавления друзей:",
        reply_markup=keyboard
    )


def minus_event_friends(message):
    """Функция команды /minuseventfriends - Удаление друзей с НЕРЕГУЛЯРНОГО ивента"""
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


@boss_only
def send_event_results_command(message):
    """Функция команды /sendevent - Ручная отправка результатов по нерегулярному ивенту бармену"""
    events = load_all_events()
    if not events:
        bot.send_message(message.chat.id, "Нет активных нерегулярных мероприятий.")
        return
    # Клавиатура выбора события
    markup = types.InlineKeyboardMarkup()
    for event in events:
        btn = types.InlineKeyboardButton(f"{event['title']} - {event['date']} {event['time']}", callback_data=f"send_event_result_{event['id']}")
        markup.add(btn)
    bot.send_message(message.chat.id, "Выберите мероприятие для отправки результатов бармену:", reply_markup=markup)


# TODO: ПЕРЕПИСАТЬ ЭТУ ТЕМУ:
def handle_send_event_result_callback(call):
    """Функция-Callback обработка выбора события для отправки результатов"""
    data = call.data
    if not data.startswith("send_event_result_"):
        return
    event_id = data.replace("send_event_result_", "")
    event = get_event_by_id(event_id)
    if not event:
        bot.answer_callback_query(call.id, "Событие не найдено", show_alert=True)
        return
    event_data = load_event_data(event_id)
    participants_count = len(event_data['participants'])
    friends_count = sum(f['count'] for f in event_data.get('friends', []))
    total_count = participants_count + friends_count
    tables = (total_count + 3) // 4
    # Отправляем бармену
    message = f"Привет! Сегодня маги решили нерегулярно собраться!\nВот столько человек придёт: {total_count} нужно {tables} столов."
    bot.send_message(BARTENDER, message)
    # Открепляем опрос
    unpin_event_poll(event_id)
    # Очищаем участников и друзей
    save_event_data(event_id, {"participants": [], "friends": []})
    bot.answer_callback_query(call.id, "Результаты отправлены бармену и очищены!", show_alert=True)
    bot.send_message(call.message.chat.id, f"Результаты по '{event['title']}' отправлены бармену и очищены.")










