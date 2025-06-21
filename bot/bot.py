import signal
import sys
import logging
from logging.handlers import RotatingFileHandler

from scheduler import run_scheduler
from handlers import register_handlers
from config import bot
from polls import restore_poll_state

# Настройка логирования
log_formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(name)s - %(message)s')

# Логирование в файл
file_handler = RotatingFileHandler('beerbot.log', maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Логирование в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Добавляем оба обработчика
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Убираем стандартный обработчик, чтобы избежать дублирования
logging.getLogger('__main__').propagate = False
logging.getLogger('utils').propagate = False
logging.getLogger('polls').propagate = False
logging.getLogger('scheduler').propagate = False
logging.getLogger('commands').propagate = False
logging.getLogger('callbacks').propagate = False
logging.getLogger('permissions').propagate = False


def signal_handler(sig, frame):
    logger.info('Завершение работы бота...')
    bot.stop_polling()
    sys.exit(0)
    
    
# Значит жить можно.
if __name__ == '__main__':
    # Регистрируем обработчики команд
    register_handlers()
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info('Восстановление состояния опроса...')
        restore_poll_state(bot)
        
        logger.info('Запуск планировщика...')
        run_scheduler()
        
        logger.info('Бот запущен...')
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        logger.error(f'Ошибка при запуске бота: {e}', exc_info=True)
        sys.exit(1)