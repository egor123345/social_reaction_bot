from telebot import types
from markup_construct import create_markup
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd
from pandas import ExcelWriter
from datetime import datetime, timedelta
import xlsxwriter
import os
import json
from graph_builder import *
from random import randint


def welcome_handler(message, bot):
    items = ['Анализ сообщества в Vk', "Анализ поста в Vk"]
    markup = create_markup(items)
    bot.send_message(message.chat.id, "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, "
                        "бот, созданный для анализа социального отклика на информационное воздействие, " 
                        "осуществляемое через социальную сеть \"Вконтакте\"".format(message.from_user, bot.get_me())
                        , parse_mode='html', reply_markup=markup)

def choose_stat(message, gr_posts, bot):
    if message.chat.type == 'private':
        stats = ["likes", "comments", "reposts"]
        but_stat_name = ["Лайки", "Комментарии", "Репосты"]
        if (message.text  in but_stat_name):
            stat_dict = {}
            for i, stat in enumerate(but_stat_name):
                stat_dict[stat] = stats[i]

            items = ["Значения относительно просмотров(%)", "Абсолютные значения"]
            markup = create_markup(items)
            msg =  bot.send_message(message.chat.id, "Выберите опцию анализа", reply_markup=markup)
            bot.register_next_step_handler(msg, choose_opt_analys, gr_posts, stat_dict[message.text], bot)
        else:
            msg = bot.send_message(message.chat.id, "Выберите показатель для анализа")
            bot.register_next_step_handler(msg, choose_stat, gr_posts, bot)

def choose_opt_analys(message, gr_posts, stat, bot):
    if message.chat.type == 'private':
        if message.text == "Значения относительно просмотров(%)" or message.text =="Абсолютные значения":
            metric = stat +  "_perc"
            if (message.text =="Абсолютные значения"):
                metric = "absol_" + stat
            
            items = ["Самый популярный пост", "Самый непопулярный пост" , "График популярности постов",
                                            "Записи за определенный период",  "Назад"]
            markup = create_markup(items)
            msg = bot.send_message(message.chat.id, "Выберите опцию анализа", reply_markup=markup)
            temp_gr_posts = list(gr_posts)
            bot.register_next_step_handler(msg, pop_analys, gr_posts, temp_gr_posts, metric, bot)
        else:
            msg = bot.send_message(message.chat.id, "Выберите опцию анализа")
            bot.register_next_step_handler(msg, choose_opt_analys, gr_posts, message.text, bot)


def pop_analys(message, gr_posts, temp_gr_posts, metric, bot):
    if message.chat.type == 'private':
        if message.text == 'Самый популярный пост':
            msg = send_extreme_post(max, temp_gr_posts, message, metric, bot)
        elif message.text == 'Самый непопулярный пост':
            msg = send_extreme_post(min, temp_gr_posts, message, metric, bot)
        elif message.text == 'График популярности постов':
            metric_data = list(map(lambda post: post[metric], gr_posts))
            date = list(map(lambda post: datetime.fromtimestamp(post["date"]), gr_posts))
            
            gr_labels = {"graph_title": "График социальной реакции аудитории на посты",
                        "xlabel":"Дата" , "ylabel": f'% {metric}'}
            msg = draw_time_graph(bot, message, gr_labels, date, metric_data)
        elif message.text == 'Записи за определенный период':
            msg = bot.send_message(message.chat.id, "Введите дату в формате \"dd-mm-yyyy\"", 
                                    reply_markup= types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, bot_get_post_by_date, gr_posts,  temp_gr_posts, metric, bot)
            return
        else:
            create_gen_opt(bot, message, "Выберите опцию анализа", gr_posts)
            return # проверить
    bot.register_next_step_handler(msg, pop_analys, gr_posts, temp_gr_posts, metric, bot)

def bot_get_post_by_date(message, gr_posts, temp_gr_posts, metric, bot):
    if message.chat.type == 'private':
        try:
            date = datetime.strptime(message.text, '%d-%m-%Y')
            goal_posts = ""
            for post in gr_posts:
                post_date = datetime.fromtimestamp(post["date"])
                if (post_date.day == date.day and post_date.month == date.month 
                             and post_date.year == date.year):
                    post_url = f'https://vk.com/wall{post["from_id"]}_{post["id"]}\n'
                    goal_posts+= post_url
            if (len(goal_posts) == 0):
                bot.send_message(message.chat.id, "Постов за выбранный период нет!")
            else:
                bot.send_message(message.chat.id, goal_posts)
            items = ["Самый популярный пост", "Самый непопулярный пост" , "График популярности постов",
                                                "Записи за определенный период",  "Назад"]
            markup = create_markup(items)
            msg = bot.send_message(message.chat.id, "Выберите опцию анализа", reply_markup=markup)
            bot.register_next_step_handler(msg, pop_analys, gr_posts, temp_gr_posts, metric, bot)
        except ValueError:
            msg = bot.send_message(message.chat.id, "Введите корректную дату в формате \"dd-mm-yyyy\"")
            bot.register_next_step_handler(msg, bot_get_post_by_date, gr_posts, temp_gr_posts, metric, bot)
       


# def get_post_by_date(date, gr_posts):

# если нет постов то сообщение если есть то пост \n пост \n
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


def send_extreme_post(extr_foo, temp_gr_posts, message, metric, bot):
    if (len(temp_gr_posts) == 0):
         msg = bot.send_message(message.chat.id, "Посты закончились")
         return msg
    post = extr_foo(temp_gr_posts, key = lambda post: post[metric])
    post_url = f'https://vk.com/wall{post["from_id"]}_{post["id"]}'
    temp_gr_posts.remove(post)
    msg = bot.send_message(message.chat.id, post_url)
    return msg

def create_gen_opt(bot, message, bot_msg_text, gr_posts):
    items = ["Анализ популярности постов", "Выгрузка данных" , "Анализ типа контента", "Сравнение с другой группой", "Выход"]
    markup = create_markup(items)

    msg = bot.send_message(message.chat.id, bot_msg_text, reply_markup=markup)
    bot.register_next_step_handler(msg, group_analys_opt, gr_posts, bot)




def groups_to_pd(gr_posts):
    group_df = pd.DataFrame(gr_posts, columns=["absol_likes", "absol_reposts", "absol_comments",
                         'likes_perc', 'reposts_perc', 'comments_perc'])

    is_text_arr = list(map(lambda post: int(bool(post["text"])), gr_posts))
    group_df["is_text"] = is_text_arr

    group_df["photo_cnt"] = check_attachment(gr_posts, "photo")
    group_df["video_cnt"] = check_attachment(gr_posts, "video")

    return group_df

def check_attachment(gr_posts, attach_type):
    attac_arr = []
    for post in gr_posts:
        att_cnt = 0
        if ("attachments" in post):
            for att in post["attachments"]:
                if att["type"] == attach_type:
                    att_cnt+= 1
        attac_arr.append(att_cnt)
    return attac_arr

def group_analys_opt(message, gr_posts, bot):
    group_df = groups_to_pd(gr_posts)
    if message.chat.type == 'private':
        if message.text == 'Анализ популярности постов':
            items = ["Лайки", "Репосты", "Комментарии"]
            # callback_data_arr = ["likes", "reposts", "comments"]
            markup = create_markup(items)
            msg = bot.send_message(message.chat.id, "Выберите показатель для анализа", reply_markup=markup)
            bot.register_next_step_handler(msg, choose_stat, gr_posts, bot)
            # bot.register_next_step_handler(msg, message, gr_posts)
            # items = ["Самый популярный пост", "Самый непопулярный пост" , "График популярности постов", "Назад"]
            # markup = create_markup(items)
            # msg = bot.send_message(message.chat.id, "Выберите опцию анализа", reply_markup=markup)
            # temp_gr_posts = list(gr_posts)
            # bot.register_next_step_handler(msg, pop_analys, gr_posts, temp_gr_posts)
        elif message.text == "Выгрузка данных":
            items = ["json", "excel"]
            markup = create_markup(items)
            msg = bot.send_message(message.chat.id, "Выберите формат данных (excel содержит основные стастики "
                                                            "json полную информацию)", reply_markup=markup)
            bot.register_next_step_handler(msg, load_data, gr_posts, group_df, bot)
        elif message.text == "Анализ типа контента":
            fig = draw_fig_content(group_df)
            num = randint(1, 1000)
            file_path = f"gr_data/content_{num}.png"
            fig.write_image(file_path)
            msg = bot.send_photo(message.chat.id, photo=open(file_path, 'rb'))
            if os.path.isfile(file_path):
                    os.remove(file_path)
            bot.register_next_step_handler(msg, group_analys_opt, gr_posts, bot)

        else:
            msg = bot.send_message(message.chat.id, "Анализ завершен")
            welcome_handler(msg, bot)
            return
            
def load_data(message, gr_posts, group_df, bot):
    if message.chat.type == 'private':
        if (message.text == "json"):
            try:
                file_name = f'gr_data/vk_group_for_{message.chat.id}.json'
                with open(file_name, 'w+', encoding="utf-8") as outfile:
                    json.dump(gr_posts, outfile, ensure_ascii = False, indent = 2)

                with open(file_name, 'rb') as read_file:
                    msg = bot.send_document(message.chat.id, read_file)
            except BaseException  as ex:
                print(ex)
            finally:
                os.remove(file_name)
            
        elif (message.text == "excel"):
            try:
                file_name = f'gr_data/vk_group_for_{message.chat.id}.xlsx'
                writer = ExcelWriter(file_name, engine="xlsxwriter")
                group_df.to_excel(writer,'Group Vk')
                writer.save()
                with open(file_name, 'rb') as read_file:
                    msg = bot.send_document(message.chat.id, read_file) 
                os.remove(file_name)
            except BaseException  as ex:
                print(ex)

        else:
            msg =  bot.send_message(message.chat.id, "Введен некорректный формат")

        create_gen_opt(bot, message, "Выберите опцию анализа", gr_posts)
        

def add_el_to_arr_dict(gr_posts, el, el_name):
    for dict in gr_posts:
        dict[el_name] = dict[el]["count"]
    