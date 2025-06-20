from config import bot
from commands import (
    invite_link, beer_rules, greet_new_members, help_command,
    info, manual_poll, manual_gameon, manual_poll_results
)
from callbacks import callback_message
from utils import save_yes_vote

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
    
# === HANDLERS ===
    # Обработчик новых участников
    bot.message_handler(content_types=['new_chat_members'])(greet_new_members)
    
    # Обработчик текстовых сообщений
    bot.message_handler(content_types=['text'])(info)
    
    # Обработчик callback-запросов
    bot.callback_query_handler(func=lambda call: True)(callback_message)

@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    # "Да" — это индекс 0
    if 0 in poll_answer.option_ids:
        save_yes_vote(poll_answer.user)