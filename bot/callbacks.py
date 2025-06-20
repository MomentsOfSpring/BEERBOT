from telebot import types
from config import MAGIC_CHAT_ID, BOSS, BARTENDER, bot
from commands import beer_rules
from buttons import send_reservation_buttons
from utils import generate_report, clear_poll_results, clear_poll_id


def callback_message(callback):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    user_id = callback.from_user.id

    # --- Новый пользователь: проверка кнопки beer_yes / beer_no ---
    if data.startswith("beer_"):
        parts = data.split("_")
        if len(parts) != 3:
            bot.answer_callback_query(callback.id, "Некорректные данные!", show_alert=True)
            return

        action, _, user_id_str = parts
        try:
            user_id_from_button = int(user_id_str)
        except ValueError:
            bot.answer_callback_query(callback.id, "Некорректный user_id!", show_alert=True)
            return

        if user_id != user_id_from_button:
            bot.answer_callback_query(callback.id, "Остальных не спрашивали!", show_alert=True)
            return

        bot.answer_callback_query(callback.id)

        if action == "beer":
            if parts[1] == "yes":
                bot.restrict_chat_member(
                    chat_id,
                    user_id,
                    permissions=types.ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
                bot.edit_message_text("Добро пожаловать домой!", chat_id, message_id)

                full_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('📜 Правила группы', callback_data='RULES'))

                welcome_text = (
                    f"Добро пожаловать, {full_name}! 🎉\n\n"
                    f"Ознакомься с правилами группы, чтобы не получить по щам!"
                )
                bot.send_message(chat_id, welcome_text, reply_markup=markup)

            elif parts[1] == "no":
                bot.edit_message_text("У нас таких не любят..", chat_id, message_id)
                bot.kick_chat_member(chat_id, user_id)

        return

    # --- Правила группы ---
    elif data == 'RULES':
        beer_rules(callback.message)

    # --- Босс нажал "Забронировать стол" ---
    elif data == 'book_table':
        report, tables = generate_report()
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Стол забронирован! 🪑")
        try:
            if tables == 0:
                bot.send_message(MAGIC_CHAT_ID, "Реки пива на этой неделе останутся нетронутыми..")
                bot.send_message(BARTENDER, "Привет, сегодня без брони. У магов — трезвая среда.")
            else:
                bot.send_message(MAGIC_CHAT_ID, "Босс забронировал кабак!")
                bot.send_message(BOSS, "Отлично, фиксируем столы.")
                bot.send_message(BARTENDER, f"Привет, маги сегодня придут к 19:00, резервируем {tables} стола(-ов).")
            clear_poll_results()
            clear_poll_id()
        except Exception as e:
            print(f"Ошибка при отправке результата брони: {e}")

    # --- Босс нажал "Мы не придем" ---
    elif data == 'not_come':
        send_reservation_buttons(chat_id=chat_id, message_id=message_id, confirm_decline=True)

    # --- Вернуться назад из "Мы не придем" ---
    elif data == 'back_to_menu':
        send_reservation_buttons(chat_id=chat_id, message_id=message_id)

    # --- Подтверждение отказа ---
    elif data == 'sure_not_come':
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Очень жаль. Чтож, в следующий раз.")
        try:
            bot.send_message(MAGIC_CHAT_ID, "Сегодня магии не будет. Босс объявляет день трезвости... 😢")
            bot.send_message(BARTENDER, "Привет, на этой неделе магов не будет. День трезвости.")
            clear_poll_results()
            clear_poll_id()
        except Exception as e:
            print(f"Ошибка при отправке отказа бармену: {e}")