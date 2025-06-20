from config import bot
from telebot import types


# Кнопки для Сени:
def send_reservation_buttons(chat_id: int, message_id: int = None, confirm_decline: bool = False):
    if confirm_decline:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Точно не придем", callback_data='sure_not_come')
        )
        markup.add(
            types.InlineKeyboardButton("Назад", callback_data='back_to_menu')
        )
        text = "Вы уверены, что не придете?"
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Забронировать", callback_data='book_table')
        )
        markup.add(
            types.InlineKeyboardButton("Мы не придем", callback_data='not_come')
        )
        text = "Выберите действие, Босс:"

    try:
        if message_id:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=markup
            )
        else:
            bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=markup
            )
    except Exception as e:
        print(f"Ошибка при отправке кнопок Боссу: {e}")