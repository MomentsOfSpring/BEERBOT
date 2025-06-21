import time
import schedule
import threading
import logging
import pytz

from datetime import datetime, timedelta
from config import bot, BOSS, MAGIC_CHAT_ID, BARTENDER
from polls import create_poll, unpin_poll
from utils import generate_report, clear_poll_results, clear_poll_id
from buttons import send_reservation_buttons


logger = logging.getLogger(__name__)


# ============================== РАСПИСАНИЕ ==============================
# ПОНЕДЕЛЬНИК // 10:00 - Создание опроса на ближайшую среду.
#
# СРЕДА // 15:00 - Отправка результатов Боссу, Бронирование столов.
# СРЕДА // 19:00 - Пожелание хорошей игры
#
# ========================================================================
MSK = pytz.timezone('Europe/Moscow')
print(datetime.now(MSK))


def monday_ten_am():
    now = datetime.now(MSK).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] Запуск опроса в понедельник 10:00 (МСК)")
    create_poll(bot)
    bot.send_message(BOSS, "Опрос запущен автоматически (понедельник, 10:00 МСК).")


def wednesday_three_pm():
    now = datetime.now(MSK).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] Подведение итогов в среду 15:00 (МСК)")
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
        bot.send_message(BOSS, "Голосование завершено АВТОМАТИЧЕСКИ.")
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


def run_scheduler():
    schedule.every().monday.at("10:00", "Europe/Moscow").do(monday_ten_am)
    schedule.every().wednesday.at("15:00", "Europe/Moscow").do(wednesday_three_pm)

    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(10)  # Проверяем каждые 10 секунд

    threading.Thread(target=scheduler_loop, daemon=True).start()
