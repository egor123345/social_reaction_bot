# import telebot
# from markup_construct import *

# def callback_inline_handler(bot, call):
#     if call.message:
#         if call.data in ["likes", "comments", "reposts"]:
#             items = ["Значения относительно просмотров в %", "Абсолютные значения"]
#             callback_arr = [f'perc_val-{call.data}', f'absol_val-{call.data}']
#             markup = create_inline_markup(items, callback_arr)
#             msg = bot.send_message(call.message.chat.id, "Выберите измерение", reply_markup=markup)
#             bot.delete_message(call.from_user.id, call.message.json['message_id'])

#         if call.data.startswith("perc_val") or call.data.startswith("absol_val"):
#             del_ind = call.data.rfind('-')
#             metric = call.data[del_ind + 1 :] + "_perc"
#             if (call.data.startswith("absol_val")):
#                 metric = "absol_" + call.data[del_ind + 1 :]
#             items = ["Самый популярный пост", "Самый непопулярный пост" , "График популярности постов", "Назад"]
#             markup = create_markup(items)
#             msg = bot.send_message(call.message.chat.id, "Выберите опцию анализа", reply_markup=markup)
#             # temp_gr_posts = list(gr_posts)
#             bot.register_next_step_handler(msg, pop_analys, gr_posts, temp_gr_posts, metric, bot)


#         bot.delete_message(call.from_user.id, call.message.json['message_id'])
        


