import telebot
import config
import json
import requests
from telebot import types
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import DateFormatter
from datetime import datetime, timedelta
import os


bot = telebot.TeleBot(config.TOKEN)
VK_TOKEN = config.HASH

# plt.plot([1,2,3,4])
# # plt.show()
# plt.savefig('saved_figure.png')

# ОТФИЛЬТРОВАТЬ РЕКЛАМНЫЕ ПОСТЫ (МБ ЕСТЬ МЕТКА УЗНАТЬ)
# вЫНЕСТИ 2 ФУНКЦИИ ЗАПРОСА К ВК В ФАЙЛ ДРУГОЙ
def create_markup(items):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(*items)
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    items = ['Анализ сообщества в Vk', "Анализ поста в Vk"]
    markup = create_markup(items)
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
    if ("is_pinned" in gr_posts[0] and gr_posts[0]["is_pinned"] == True):
        gr_posts.pop(0)
    for i, post in enumerate(gr_posts):
        gr_posts[i]["likes_perc"] = post["likes"]["count"] / post["views"]["count"] * 100
        gr_posts[i]["reposts_perc"] = post["reposts"]["count"] / post["views"]["count"] * 100
        gr_posts[i]["comments_perc"] = post["comments"]["count"] / post["views"]["count"] * 100
        
    # print(max(gr_posts, key = lambda post: post["likes_perc"])) ПОИСК MAX
    create_gen_opt(bot, message, "Выберите опцию", gr_posts)

def create_gen_opt(bot, message, bot_msg_text, gr_posts):
    items = ["Анализ популярности постов", "Заглушка1" , "Заглушка2", "Выход"]
    markup = create_markup(items)

    msg = bot.send_message(message.chat.id, bot_msg_text, reply_markup=markup)
    bot.register_next_step_handler(msg, group_analys_opt, gr_posts)


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

def group_analys_opt(message, gr_posts):
    if message.chat.type == 'private':
        if message.text == 'Анализ популярности постов':
            items = ["Самый популярный пост", "Самый непопулярный пост" , "График популярности постов", "Назад"]
            markup = create_markup(items)
            msg = bot.send_message(message.chat.id, "Выберите опцию анализа", reply_markup=markup)
            temp_gr_posts = list(gr_posts)
            bot.register_next_step_handler(msg, pop_analys, gr_posts, temp_gr_posts)
        # elif
        else:
            msg = bot.send_message(message.chat.id, "Анализ завершен")
            welcome(msg)
            return

def pop_analys(message, gr_posts, temp_gr_posts):
    if message.chat.type == 'private':
        if message.text == 'Самый популярный пост':
            msg = send_extreme_post(max, temp_gr_posts, message)
        elif message.text == 'Самый непопулярный пост':
            msg = send_extreme_post(min, temp_gr_posts, message)
        elif message.text == 'График популярности постов':
            likes_perc_arr = list(map(lambda post: post["likes_perc"], gr_posts))
            date = list(map(lambda post: datetime.fromtimestamp(post["date"]), gr_posts))
            short_date = list(map(lambda d: datetime(d.year, d.month, d.day), date))
            gr_labels = {"graph_title": "График социальной реакции аудитории на посты",
                        "xlabel":"Дата" , "ylabel": "% Лайков от общей аудитории"}
            msg = draw_time_graph(bot, message, gr_labels, date, likes_perc_arr)
        else:
            create_gen_opt(bot, message, "Выберите опцию анализа", gr_posts)
            return
    bot.register_next_step_handler(msg, pop_analys, gr_posts, temp_gr_posts)

def draw_time_graph(bot, message, gr_labels, date, y_data, width = 12, height = 8):
    bot.send_message(message.chat.id, gr_labels["graph_title"])
    fig, ax = plt.subplots()
    fig.set_figwidth(width)
    fig.set_figheight(height)

    plt.xlabel(gr_labels["xlabel"])
    plt.ylabel(gr_labels["ylabel"])
    myFmt = DateFormatter("%d-%m-%y")
    ax.xaxis.set_major_formatter(myFmt)
    fig.suptitle(gr_labels["graph_title"], fontweight ="bold")

    step =  (max(date) - min(date)) / 10
    if (step.days != 0):
        step = timedelta(days = step.days)
    xticks = np.arange(min(date), max(date) + step, step).astype(datetime)
  
    xticks = list(set(map(lambda d: datetime(d.year, d.month, d.day), xticks)))
    plt.xticks(xticks)
    plt.plot(date, y_data) 
    ax.set_xlim([min(date), max(date)])
    plt.savefig('graphs/time_graph.png')
    msg = bot.send_photo(message.chat.id, photo=open('graphs/time_graph.png', 'rb'))
    if os.path.isfile('graphs/time_graph.png'):
            os.remove('graphs/time_graph.png')
    return msg


def send_extreme_post(extr_foo, temp_gr_posts, message):
    if (len(temp_gr_posts) == 0):
         msg = bot.send_message(message.chat.id, "Посты закончились")
         return msg
    post = extr_foo(temp_gr_posts, key = lambda post: post["likes_perc"])
    post_url = f'https://vk.com/wall{post["from_id"]}_{post["id"]}'
    temp_gr_posts.remove(post)
    msg = bot.send_message(message.chat.id, post_url)
    return msg

# RUN
print("RUN!")

bot.polling(none_stop=True)
