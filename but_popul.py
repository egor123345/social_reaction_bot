import imp
from telebot import types
from markup_construct import create_markup
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd
from pandas import ExcelFile, ExcelWriter
from datetime import datetime, timedelta
import xlsxwriter
import os
import requests
import json
from graph_builder import *
from random import randint
from mat import calc_ban_words, read_words_from_file
from parse_vk import *
from bot_send_file import send_plotly_img_by_bot
from toxicity import ToxicCommentsDetector


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
                        "xlabel":"Дата" , "ylabel": f' {metric}'}
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
       

def draw_time_graph(bot, message, gr_labels, date, y_data, width = 12, height = 8):
    bot.send_message(message.chat.id, gr_labels["graph_title"])
    plt.ioff()
    fig, ax = plt.subplots()
    fig.set_figwidth(width)
    fig.set_figheight(height)

    ax.set_xlabel(gr_labels["xlabel"])
    ax.set_ylabel(gr_labels["ylabel"])
    myFmt = DateFormatter("%d-%m-%y")
    ax.xaxis.set_major_formatter(myFmt)
    fig.suptitle(gr_labels["graph_title"], fontweight ="bold")

    step =  (max(date) - min(date)) / 10
    if (step.days != 0):
        step = timedelta(days = step.days)
    xticks = np.arange(min(date), max(date) + step, step).astype(datetime)
  
    xticks = list(set(map(lambda d: datetime(d.year, d.month, d.day), xticks)))
    ax.set_xticks(xticks)
    ax.plot(date, y_data) 
    ax.set_xlim([min(date), max(date)])
    fig.savefig('graphs/time_graph.png')
    fig.clear()
  
    time_graph = open('graphs/time_graph.png', 'rb')
    msg = bot.send_photo(message.chat.id, photo=time_graph)
    time_graph.close()
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
            markup = create_markup(items)
            msg = bot.send_message(message.chat.id, "Выберите показатель для анализа", reply_markup=markup)
            bot.register_next_step_handler(msg, choose_stat, gr_posts, bot)
        elif message.text == "Выгрузка данных":
            items = ["json", "excel"]
            markup = create_markup(items)
            msg = bot.send_message(message.chat.id, "Выберите формат данных (excel содержит основные статистики, "
                                                            "json полную информацию)", reply_markup=markup)
            bot.register_next_step_handler(msg, load_data, gr_posts, group_df, bot)
        elif message.text == "Корреляция между метриками":
            heat_map_path = draw_heat_map(group_df, message.chat.id)
            try:
                heat_map_path = draw_heat_map(group_df, message.chat.id)
                msg = bot.send_photo(message.chat.id, photo=open(heat_map_path, 'rb'))
                if os.path.isfile(heat_map_path):
                    os.remove(heat_map_path)
                bot.register_next_step_handler(msg, group_analys_opt, gr_posts, bot)
            except BaseException  as ex:
                    print(ex)
        elif message.text == "Анализ типа контента":
            fig = draw_fig_content(group_df)
            num = randint(1, 1000)
            file_path = f"gr_data/content_{num}.png"
            msg = send_plotly_img_by_bot(file_path, fig, message, bot)
            bot.register_next_step_handler(msg, group_analys_opt, gr_posts, bot)
        elif message.text == "Сравнение с другой группой":
            msg = bot.send_message(message.chat.id, "Введите адрес сообщества Вконтакте", 
                            reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, get_group_to_cmp, gr_posts, bot)
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
        
def create_gen_opt(bot, message, bot_msg_text, gr_posts):
    items = ["Анализ популярности постов", "Выгрузка данных" , "Анализ типа контента", "Сравнение с другой группой",
                        "Корреляция между метриками" ,"Выход"]
    markup = create_markup(items)

    msg = bot.send_message(message.chat.id, bot_msg_text, reply_markup=markup)
    bot.register_next_step_handler(msg, group_analys_opt, gr_posts, bot)

def group_cmp(message, gr_posts, bot, cmp_gr_posts):
    try: 
        if message.chat.type == 'private':
            metrics = ["likes", "reposts", "comments"]
            if (message.text == "Абсолютные"):
                metrics = list(map(lambda metric: "absol_" + metric, metrics))
            else:
                metrics = list(map(lambda metric: metric + "_perc", metrics))
            src_gr_title = get_gr_vk_name_by_id(gr_posts[0]["owner_id"])
            src_gr_posts_df = groups_to_pd(gr_posts)

            cmp_gr_posts_df = groups_to_pd(cmp_gr_posts)
            cmp_gr_title = get_gr_vk_name_by_id(cmp_gr_posts[0]["owner_id"])
            
            fig = draw_kde_by_metrics(src_gr_posts_df, src_gr_title, 
                                cmp_gr_posts_df, cmp_gr_title, metrics)
            file_path = f"gr_data/kde_{message.chat.id}.png"

            msg = send_plotly_img_by_bot(file_path, fig, message, bot)

    except Exception as ex:
            msg = bot.send_message(message.chat.id, str(ex))
    finally:
        create_gen_opt(bot, msg, "Выберите опцию анализа", gr_posts)
    

def get_group_to_cmp(message,  gr_posts, bot):
    try:
        cmp_gr_posts = get_vk_groups_info(message)
        items = ["Абсолютные", "Процентные"]
        markup = create_markup(items)
        msg = bot.send_message(message.chat.id, "Выберите тип метрик социальной реакции для сравнения",
                                reply_markup = markup)
        bot.register_next_step_handler(msg, group_cmp, gr_posts, bot, cmp_gr_posts)

    except Exception as ex:
        msg = bot.send_message(message.chat.id, str(ex) + " Введите адрес сообщества Вконтакте для сравнения заново")
        bot.register_next_step_handler(msg, get_group_to_cmp, gr_posts, bot)

def get_gr_vk_name_by_id(id):
    id = abs(id)
    gr_name_par = {
                'access_token': config.HASH,
                'v':5.131,
                "group_id": id
    }
    res = requests.get('https://api.vk.com/method/groups.getById', gr_name_par).json()
    if ("error" in res or len(res["response"]) == 0):
        raise Exception("Не удалось получить данные о группе Vk")

    gr_name = res["response"][0]["name"]
    return gr_name

def post_analys_opt(message, comments, bot):
     if message.chat.type == 'private':
        try:
            if message.text == '% мата в комментариях':
                msg = bot.send_message(message.chat.id,  'Минутку...')
                words = read_words_from_file("C:/Users/ASUS/workspace/test/mat.txt")
                comments_list = get_comments_from_vk_com_dict(comments)
                if (len(comments_list) == 0):
                    raise Exception("Комментарии к посту отсутствуют")
                ban_words_perc, ban_word_cnt = calc_ban_words(words, comments_list)
                comments_cnt = len(comments_list)
                bot.delete_message(msg.chat.id, msg.message_id)
                msg = bot.send_message(message.chat.id, f"{ban_words_perc}% комментариев содержат нецензурную лексику\n"
                                                    f"({ban_word_cnt} из {comments_cnt} текстовых комментариев к посту)")
                bot.register_next_step_handler(msg, post_analys_opt, comments, bot)
            elif message.text == '% Токсичности в комментариях':
                msg = bot.send_message(message.chat.id,  'Минутку...')
                comments_list = get_comments_from_vk_com_dict(comments)
                if (len(comments_list) == 0):
                    raise Exception("Комментарии к посту отсутствуют")
                toxicDetector = ToxicCommentsDetector()
                k_toxic_arr = toxicDetector.predict(comments_list)
                # print(k_toxic_arr)
                # print(list(map(lambda com, perc: com + ":" + str(perc) + '%', comments_list, k_toxic_arr)))
                k_toxic_arr = np.array(k_toxic_arr)
                toxic_mean_perc = round(k_toxic_arr.mean() * 100, 2)
                bot.delete_message(msg.chat.id, msg.message_id)
                msg = bot.send_message(message.chat.id, f"Средний процент токсичности в комментариях составляет {toxic_mean_perc}%\n"
                                f"Всего было проанализировано {len(comments_list)} текстовых комментариев к посту)")
                    
                bot.register_next_step_handler(msg, post_analys_opt, comments, bot)
              
            else:
                msg = bot.send_message(message.chat.id, "Анализ завершен")
                welcome_handler(msg, bot)
                return
        except Exception as ex:
                msg = bot.send_message(message.chat.id, str(ex) + " \nАнализ завершен")
                welcome_handler(msg, bot)

def get_comments_from_vk_com_dict(comments):
    comments_list = []
    for com in comments:
        if (len(com["text"]) != 0):
            comments_list.append(com["text"])
        # print(com)
        if (com["thread"]["count"] > 10):
            com_params = {
                'access_token': VK_TOKEN,
                'v':5.131,  
                "post_id": com['post_id'],
                "owner_id": com["owner_id"],
                "count": 100,
                "comment_id": com["id"],
                "thread_items_count": 10
            }
            res = requests.get("https://api.vk.com/method/wall.getComments", com_params).json()
            if ("error" in res or len(res["response"]) == 0):
                raise Exception("Не удалось получить вложенные комментарии")
            nested_coms = res["response"]["items"]
            for nested_com in nested_coms:
                if (len(nested_com["text"]) != 0):
                    comments_list.append(nested_com["text"])
        else:
            for nested_com in com["thread"]["items"]:
                if (len(nested_com["text"]) != 0):
                    comments_list.append(nested_com["text"])
    return comments_list
