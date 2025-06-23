import os
import logging

from telebot import types
from permissions import boss_only
from config import bot, BOSS, PHOTOS, RULES_FILE, HELP_FILE, INVITE, MAGIC_CHAT_ID, BARTENDER
from polls import create_poll, unpin_poll
from utils import generate_report, clear_poll_results, clear_poll_id, load_yes_votes, set_friends, remove_friends
from buttons import send_reservation_buttons
from state import user_states


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
            bot.send_message(message.chat.id, "Произошла ошибка при отправке изображений")
    
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
          or "цедх" in message.text.lower()
          or "цдх" in message.text.lower())
          or "компот" in message.text.lower()
          or "компетитив" in message.text.lower()):
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
                bot.send_message(message.chat.id, f"Отлично! Зафиксировал тебе {count} корешей.\nКоличество гедонистов-лудоманом неумолимо растет!\nТак держать!")

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


# ============================== КОМАНДЫ РУЧНОГО ЗАПУСКА ==============================

# Обработка команды /pollnow
@boss_only
def manual_poll(message):
    """СОЗДАТЬ ОПРОС ВРУЧНУЮ"""
    create_poll(bot)
    bot.send_message(BOSS, "Опрос запущен вручную.")


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








