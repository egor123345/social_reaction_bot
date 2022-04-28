from telebot import types

def create_markup(items):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(*items)
    return markup

def create_inline_markup(items, callback_data_arr):
    markup = types.InlineKeyboardMarkup(row_width=2)
    inl_items = []
    for i, item in enumerate(items):
        inl_items.append(types.InlineKeyboardButton(item, callback_data=callback_data_arr[i]))
    
    markup.add(*inl_items)
    return markup

