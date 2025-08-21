from telebot import types
from config import MAGIC_CHAT_ID, BOSS, BARTENDER, bot, BOSSES
from commands import beer_rules
from buttons import send_reservation_buttons
from utils import generate_report, clear_poll_results, clear_poll_id
from events import get_confirmation_keyboard, delete_event, send_event_cancellation_notification, unpin_event_poll, handle_event_poll_answer
from state import user_states


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
                bot.edit_message_text("Добро пожаловать домой, Друг! 🎉", chat_id, message_id)

                full_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('📜 Правила группы', callback_data='RULES'))

                welcome_text = (
                    f"Добро пожаловать, {full_name}!\n\n"
                    f"Ознакомься с правилами группы, чтобы не получить по щам!"
                )
                bot.send_message(chat_id, welcome_text, reply_markup=markup)

            elif parts[1] == "no":
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
                bot.edit_message_text("Добро пожаловать, конечно, но сразу скажу, у нас таких не любят..", chat_id, message_id)

                full_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton('📜 Правила группы', callback_data='RULES'))

                welcome_text = (
                    f"Добро пожаловать, {full_name}!\n\n"
                    f"Ознакомься с правилами группы, чтобы не получить по щам!"
                )
                bot.send_message(chat_id, welcome_text, reply_markup=markup)

        return

    # --- Правила группы ---
    elif data == 'RULES':
        beer_rules(callback.message)

    # --- Удаление события: выбор события ---
    elif data.startswith("delete_event_"):
        if user_id not in BOSSES:  # Только боссы могут удалять события
            bot.answer_callback_query(callback.id, "У вас нет прав для удаления событий!", show_alert=True)
            return
            
        event_id = data.replace("delete_event_", "")
        keyboard = get_confirmation_keyboard(event_id)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Точно удалить ивент?",
            reply_markup=keyboard
        )

    # --- Подтверждение удаления события ---
    elif data.startswith("confirm_delete_"):
        if user_id not in BOSSES:  # Только боссы могут удалять события
            bot.answer_callback_query(callback.id, "У вас нет прав для удаления событий!", show_alert=True)
            return
            
        event_id = data.replace("confirm_delete_", "")
        
        # Отправляем уведомление об отмене
        send_event_cancellation_notification(event_id)
        
        # Открепляем опрос
        unpin_event_poll(event_id)
        
        # Удаляем событие
        if delete_event(event_id):
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="✅ Событие удалено!"
            )
        else:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Ошибка при удалении события!"
            )

    # --- Отмена удаления события ---
    elif data == "cancel_delete":
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Удаление отменено."
        )

    # --- Выбор события для добавления/удаления друзей ---
    elif data.startswith("event_friends_"):
        event_id = data.replace("event_friends_", "")
        
        # Получаем текущее состояние пользователя
        key = (user_id, chat_id)
        if key not in user_states:
            bot.answer_callback_query(callback.id, "Ошибка: состояние не найдено", show_alert=True)
            return
            
        state = user_states[key]
        if state["state"] != "waiting_event_friends":
            bot.answer_callback_query(callback.id, "Ошибка: неверное состояние", show_alert=True)
            return
        
        # Сохраняем выбранное событие
        state["event_id"] = event_id
        user_states[key] = state
        
        # Получаем информацию о событии
        from events import get_event_by_id
        event = get_event_by_id(event_id)
        
        if not event:
            bot.answer_callback_query(callback.id, "Событие не найдено", show_alert=True)
            user_states.pop(key, None)
            return
        
        action_type = "добавления" if state["type"] == "set" else "удаления"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"Выбрано событие: {event['title']} - {event['date']} {event['time']}\n\nСколько друзей {action_type}? Введи число."
        )

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
                bot.send_message(MAGIC_CHAT_ID, report)
                bot.send_message(BOSS, "Отлично, фиксируем столы.")
                bot.send_message(BARTENDER, f"Привет, маги сегодня придут к 19:00, резервируем {tables} стола(-ов).")
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

    # --- Ручная отправка результатов по нерегулярному ивенту ---
    elif data.startswith('send_event_result_'):
        from events import get_event_by_id, load_event_data, unpin_event_poll, save_event_data, delete_event
        event_id = data.replace('send_event_result_', '')
        event = get_event_by_id(event_id)
        if not event:
            bot.answer_callback_query(callback.id, 'Событие не найдено', show_alert=True)
            return
        event_data = load_event_data(event_id)
        participants_count = len(event_data['participants'])
        friends_count = sum(f['count'] for f in event_data.get('friends', []))
        total_count = participants_count + friends_count
        tables = (total_count + 3) // 4
        message = f'Привет! Сегодня маги решили нерегулярно собраться!\nВот столько человек придёт: {total_count} нужно {tables} столов.\nВремя сбора: {event["date"]} {event["time"]}'
        bot.send_message(BARTENDER, message)
        unpin_event_poll(event_id)
        save_event_data(event_id, {'participants': [], 'friends': []})
        delete_event(event_id)
        bot.answer_callback_query(callback.id, 'Результаты отправлены бармену, ивент удалён!', show_alert=True)
        bot.send_message(callback.message.chat.id, f"Результаты по '{event['title']}' отправлены бармену и ивент удалён.")
        return


def handle_poll_answer_callback(poll_answer):
    """Обработчик ответов в опросах"""
    # Проверяем, является ли это опросом события
    from events import load_all_events
    events = load_all_events()
    
    for event in events:
        if event.get('poll_id') == poll_answer.poll_id:
            # Это опрос события
            handle_event_poll_answer(poll_answer)
            return
    
    # Если не нашли событие, это обычный опрос
    from polls import handle_poll_answer
    handle_poll_answer(poll_answer)