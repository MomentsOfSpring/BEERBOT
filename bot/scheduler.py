import time
import schedule
import threading
import logging
import pytz

from datetime import datetime, timedelta, time as dt_time
from config import bot, BOSS, MAGIC_CHAT_ID, BARTENDER
from polls import create_poll, unpin_poll
from utils import generate_report, clear_poll_results, clear_poll_id
from buttons import send_reservation_buttons
from task_state import was_task_already_run, update_last_run, clear_state


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
        clear_state()
        return

    try:
        bot.send_message(BOSS, "Голосование завершено АВТОМАТИЧЕСКИ.")
        bot.send_message(BOSS, report)
        send_reservation_buttons(BOSS)
        bot.send_message(
            MAGIC_CHAT_ID,
            "Голосование завершено.\nВсем проголосовавшим летит плотная респектуля.\nРезультаты опроса отправлены Боссу."
        )
        clear_state()
    except Exception as e:
        print(f"Ошибка при отправке результатов Боссу: {e}")
        try:
            bot.send_message(BOSS, "Ошибка при отправке результатов, Босс.")
        except:
            pass


def run_scheduler():
    schedule.every().monday.at("10:00", "Europe/Moscow").do(lambda: (monday_ten_am(), update_last_run("poll_created")))
    schedule.every().wednesday.at("15:00", "Europe/Moscow").do(lambda: (wednesday_three_pm(), update_last_run("results_sent")))

    check_missed_tasks()

    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(10)  # Проверяем каждые 10 секунд

    threading.Thread(target=scheduler_loop, daemon=True).start()


def check_missed_tasks():
    now = datetime.now(MSK)

    # --- Проверка задачи для понедельника (10:00) ---
    last_monday = now - timedelta(days=now.weekday())
    last_monday_10_am = last_monday.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # Если сегодня понедельник и время еще не 10, то последним был понедельник на прошлой неделе
    if now.weekday() == 0 and now.time() < dt_time(10, 0):
        last_monday_10_am -= timedelta(days=7)

    if not was_task_already_run("poll_created", last_monday_10_am):
        print(f"Пропущен опрос от {last_monday_10_am.strftime('%Y-%m-%d')}. Запускаем...")
        monday_ten_am()
        update_last_run("poll_created")

    # --- Проверка задачи для среды (15:00) ---
    days_since_wednesday = (now.weekday() - 2) % 7
    last_wednesday = now - timedelta(days=days_since_wednesday)
    last_wednesday_3_pm = last_wednesday.replace(hour=15, minute=0, second=0, microsecond=0)

    # Если сегодня среда и время еще не 15, то последней была среда на прошлой неделе
    if now.weekday() == 2 and now.time() < dt_time(15, 0):
        last_wednesday_3_pm -= timedelta(days=7)

    if not was_task_already_run("results_sent", last_wednesday_3_pm):
        print(f"Пропущен отчёт от {last_wednesday_3_pm.strftime('%Y-%m-%d')}. Запускаем...")
        wednesday_three_pm()
        update_last_run("results_sent")