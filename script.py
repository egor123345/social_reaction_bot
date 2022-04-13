import telebot
import config
import json
import requests
from telebot import types
import matplotlib.pyplot as plt

bot = telebot.TeleBot(config.TOKEN)
VK_TOKEN = config.HASH

# plt.plot([1,2,3,4])
# # plt.show()
# plt.savefig('saved_figure.png')

# ОТФИЛЬТРОВАТЬ РЕКЛАМНЫЕ ПОСТЫ (МБ ЕСТЬ МЕТКА УЗНАТЬ)
# вЫНЕСТИ 2 ФУНКЦИИ ЗАПРОСА К ВК В ФАЙЛ ДРУГОЙ
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items = ['Анализ сообщества в Vk', "Анализ поста в Vk"]
    markup.add(*items)
    bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, "
                        "бот, созданный для анализа социального отклика на информационное воздействие, " 
                        "осуществляемое через социальную сеть \"Вконтакте\"".format(message.from_user, bot.get_me())
                        , parse_mode='html', reply_markup=markup)
                    

@bot.message_handler(content_types=["text"])
def lalala(message):
    if message.chat.type == 'private':
        if message.text == 'Анализ сообщества в Vk':
            msg = bot.send_message(message.chat.id, "Введите адрес сообщества Вконтакте")
            bot.register_next_step_handler(msg, handle_but_click_group)

        elif message.text == 'Анализ поста в Vk':
            msg = bot.send_message(message.chat.id, "Введите адрес поста Вконтакте \n"
                                                    "(Нажмите поделиться постом -> Экспортировать -> Прямая ссылка)")
            bot.register_next_step_handler(msg, handle_but_click_post)
        else:
            bot.send_message(message.chat.id, "Это выходит за рамки моего функционала")

def handle_but_click_group(message):
    start_index = (message.text).rfind('/') + 1
    gr_domain = (message.text)[start_index :]
    gr_name_par = {
                'access_token': VK_TOKEN,
                'v':5.131,
                "screen_name": gr_domain}
    owner_id = requests.get('https://api.vk.com/method/utils.resolveScreenName', gr_name_par).json()
    if (len(owner_id["response"]) == 0):
        bot.send_message(message.chat.id, "Не удалось получить данные о группе Vk")
        return

    input_type = owner_id["response"]["type"]
    owner_id = owner_id["response"]["object_id"]
    if (input_type == "group"):
        owner_id*= -1

    params={
                'access_token': VK_TOKEN,
                'v':5.131,
                "owner_id": owner_id,
                "count": 100 #  ПОСТАВИТЬ МАКСИМУМ
    }

    gr_posts = requests.get('https://api.vk.com/method/wall.get', params=params)
    gr_posts_info = gr_posts.json()
    if (hasattr(gr_posts_info, "error")): 
        bot.send_message(message.chat.id, "Не удалось получить данные о группе Vk")
        return
    gr_posts = gr_posts_info["response"]['items']
    if (len(gr_posts) == 0):
        bot.send_message(message.chat.id, "Не удалось получить данные о группе Vk")
        return
    for i, post in enumerate(gr_posts):
        gr_posts[i]["likes_perc"] = post["likes"]["count"] / post["views"]["count"] * 100
        gr_posts[i]["reposts_perc"] = post["reposts"]["count"] / post["views"]["count"] * 100
        gr_posts[i]["comments_perc"] = post["comments"]["count"] / post["views"]["count"] * 100
        
    # print(max(gr_posts, key = lambda post: post["likes_perc"])) ПОИСК MAX
    print(list(map(lambda post: post["likes_perc"], gr_posts)))
    bot.send_message(message.chat.id, 'ECG')

def handle_but_click_post(message):
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
        bot.send_message(message.chat.id, "Не удалось получить данные о посте Vk")
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
            "thread_items_count":10
    }
    comments = requests.get("https://api.vk.com/method/wall.getComments", com_params)
    if (comments.status_code != 200):
        bot.send_message(message.chat.id, "Не удалось получить данные о комментариях к посту Vk")
        return
    comments_info = comments.json()
    comments = comments_info["response"]["items"] # Вложенные коментарии в массиве в поле thread
    bot.send_message(message.chat.id, "Заглушечка")
# RUN
print("RUN!")

bot.polling(none_stop=True)
