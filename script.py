import telebot
import config
import json
from but_popul import *
bot = telebot.TeleBot(config.TOKEN)
VK_TOKEN = config.HASH

@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_handler(message, bot)
    
# @bot.callback_query_handler(func=lambda call: True)
# def callback_inline(call):
#     callback_inline_handler(bot, call)

@bot.message_handler(content_types=["text"])
def lalala(message):
    if message.chat.type == 'private':
        if message.text == 'Анализ сообщества в Vk':
            msg = bot.send_message(message.chat.id, "Введите адрес сообщества Вконтакте",
                     reply_markup = types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, handle_but_click_group)

        elif message.text == 'Анализ поста в Vk':
            msg = bot.send_message(message.chat.id, "Введите адрес поста Вконтакте \n"
                                                    "(Нажмите поделиться постом -> Экспортировать -> Прямая ссылка)",
                                                    reply_markup = types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, handle_but_click_post)
        else:
            bot.send_message(message.chat.id, "Это выходит за рамки моего функционала")

def handle_but_click_group(message):
    try: 
        gr_posts = get_vk_groups_info(message)
        create_gen_opt(bot, message, "Выберите опцию", gr_posts)
    except Exception as ex:
        start_items = ['Анализ сообщества в Vk', "Анализ поста в Vk"]
        start_markup = create_markup(start_items)
        bot.send_message(message.chat.id, str(ex), reply_markup=start_markup)




def handle_but_click_post(message):
    start_items = ['Анализ сообщества в Vk', "Анализ поста в Vk"]
    start_markup = create_markup(start_items)

    key_word = "wall"
    ind = (message.text).rfind(key_word) 
    start_index = 0
    if (ind != -1):
        start_index = ind + len(key_word)
    full_post_id = message.text[start_index :]

    wall_params = {
                'access_token': VK_TOKEN,
                'v':5.131,
                "posts": full_post_id,
                "extended" : 1
    }
    post = requests.get('https://api.vk.com/method/wall.getById', params=wall_params)
    post_info = post.json()
    if (len(post_info["response"]["items"]) == 0):
        bot.send_message(message.chat.id, "Не удалось получить данные о посте Vk", reply_markup=start_markup)
        return
    post = post_info["response"]["items"][0]
    group = post_info["response"]["groups"][0]

    com_params = {
            'access_token': VK_TOKEN,
            'v':5.131,
            "post_id": post['id'],
            "owner_id": post["owner_id"],
            "need_likes": 1,
            "count": 100,
            "thread_items_count": 10
    }
    comments = requests.get("https://api.vk.com/method/wall.getComments", com_params)
    if (comments.status_code != 200):
        bot.send_message(message.chat.id, "Не удалось получить данные о комментариях к посту Vk", reply_markup=start_markup)
        return
    comments_info = comments.json()
    comments = comments_info["response"]["items"] # Вложенные коментарии в массиве в поле thread
    items = ["% мата в комментариях", "% Токсичности в комментариях", "Выход"]
    markup = create_markup(items)
    msg = bot.send_message(message.chat.id, "Выберите опцию", reply_markup=markup)
    bot.register_next_step_handler(msg, post_analys_opt, comments, bot)

# RUN
print("RUN!")
plt.ioff()

bot.polling(none_stop=True)
