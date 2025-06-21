import logging

from config import bot, MAGIC_CHAT_ID, POLL_DATA_FILE
from utils import get_next_wednesday, save_poll, load_poll

logger = logging.getLogger(__name__)


def create_poll(bot):
    wednesday_date = get_next_wednesday().strftime('%d.%m.%Y')

    try:
        poll_message = bot.send_poll(
            MAGIC_CHAT_ID,
            question=f"Магия, среда, {wednesday_date}. Придешь?",
            options=["Да", "Нет"],
            is_anonymous=False,
            allows_multiple_answers=False
        )
        logger.info(f"Опрос отправлен: message_id={poll_message.message_id} на {wednesday_date}")

        save_poll(MAGIC_CHAT_ID, poll_message.message_id)
        logger.info("Опрос сохранён")

        bot.pin_chat_message(
            MAGIC_CHAT_ID,
            poll_message.message_id,
            disable_notification=True
        )
        logger.info("Опрос закреплён")

    except Exception as e:
        logger.error(f"Ошибка при создании опроса или его закреплении: {e}")


def unpin_poll(bot):
    chat_id, message_id = load_poll()
    if not chat_id or not message_id:
        logger.warning("Не найдено сохранённого опроса для открепления.")
        return False

    try:
        bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Опрос откреплён: chat_id={chat_id}, message_id={message_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при откреплении опроса: {e}")
        return False