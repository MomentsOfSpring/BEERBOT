from functools import wraps
from config import BOSSES, bot, ADMIN

def boss_only(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if message.from_user.id not in BOSSES:
            bot.reply_to(message, "Не похож ты на босса, Сынок..")
            return
        return func(message, *args, **kwargs)
    return wrapper


def admin_only(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if message.from_user.id != ADMIN:
            bot.reply_to(message, "Эта команда доступна только администратору.")
            return
        return func(message, *args, **kwargs)
    return wrapper