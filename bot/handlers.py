from config import bot
from commands import (
    invite_link, beer_rules, greet_new_members, help_command,
    info, manual_poll, manual_gameon, manual_poll_results, plus_friends, minus_friends,
    add_event_command, delete_event_command, events_command, plus_event_friends, minus_event_friends,
    shout_command
)
from callbacks import callback_message, handle_poll_answer_callback
from utils import save_yes_vote, load_poll
from polls import handle_poll_answer as process_poll_answer

def register_handlers():
# === COMMANDS ===
    # Обработчик команды /start
    bot.message_handler(commands=['start'])(help_command)
    
    # Обработчик команды /help
    bot.message_handler(commands=['help'])(help_command)
    
    # Обработчик команды /invite
    bot.message_handler(commands=['invite'])(invite_link)
    
    # Обработчик команды /rules
    bot.message_handler(commands=['rules'])(beer_rules)
    
    # Обработчик команды /pollnow
    bot.message_handler(commands=['pollnow'])(manual_poll)
    
    # Обработчик команды /gameon
    bot.message_handler(commands=['gameon'])(manual_gameon)
    
    # Обработчик команды /pollres
    bot.message_handler(commands=['pollres'])(manual_poll_results)

    # Обработчик команды /plusfriends
    bot.message_handler(commands=['plusfriends'])(plus_friends)
    # Обработчик команды /minusfriends
    bot.message_handler(commands=['minusfriends'])(minus_friends)
    
    # Обработчик команды /addevent
    bot.message_handler(commands=['addevent'])(add_event_command)
    
    # Обработчик команды /deleteevent
    bot.message_handler(commands=['deleteevent'])(delete_event_command)
    
    # Обработчик команды /events
    bot.message_handler(commands=['events'])(events_command)
    
    # Обработчик команды /pluseventfriends
    bot.message_handler(commands=['pluseventfriends'])(plus_event_friends)
    
    # Обработчик команды /minuseventfriends
    bot.message_handler(commands=['minuseventfriends'])(minus_event_friends)
    
    # Обработчик команды /shout
    bot.message_handler(commands=['shout'])(shout_command)
    
# === HANDLERS ===
    # Обработчик новых участников
    bot.message_handler(content_types=['new_chat_members'])(greet_new_members)
    
    # Обработчик текстовых сообщений
    bot.message_handler(content_types=['text'])(info)
    
    # Обработчик callback-запросов
    bot.callback_query_handler(func=lambda call: True)(callback_message)

@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    # Используем новый обработчик, который поддерживает события
    handle_poll_answer_callback(poll_answer)