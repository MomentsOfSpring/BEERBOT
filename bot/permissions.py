from functools import wraps
from config import BOSSES

def boss_only(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if message.from_user.id not in BOSSES:
            message.reply("Не похож ты на босса, Сынок..")
            return
        return func(message, *args, **kwargs)
    return wrapper