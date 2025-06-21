import signal
import sys
import logging

from scheduler import run_scheduler
from handlers import register_handlers
from config import bot
from polls import restore_poll_state

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - %(levelname)s - %(name)s - %(message)s'
)


logger = logging.getLogger(__name__)


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