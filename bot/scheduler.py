from datetime import datetime, timedelta
import time
import logging


logger = logging.getLogger(__name__)


# ============================== РАСПИСАНИЕ ==============================
# ПОНЕДЕЛЬНИК // 10:00 - Создание опроса на ближайшую среду.
#
# СРЕДА // 15:00 - Отправка результатов Боссу, Бронирование столов.
# СРЕДА // 19:00 - Пожелание хорошей игры
#
# ========================================================================


# Функция получения следующей среды для создания опроса:
def get_next_wednesday():
    today = datetime.now()
    days_ahead = (2 - today.weekday()) % 7  # 2 = среда
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def schedule():
    """Основной планировщик задач"""
    logger.info("Запуск планировщика задач")
    last_monday_run = None
    last_wednesday_run = None

    while True:
        try:
            now = datetime.now()
            time.sleep(10)

        except Exception as e:
            logger.error(f"Критическая ошибка в планировщике: {e}", exc_info=True)
            time.sleep(60)  # Увеличенная пауза при ошибке