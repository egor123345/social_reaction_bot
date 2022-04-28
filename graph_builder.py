from random import random
import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import kaleido
import pandas as pd
import numpy as np
from heatmap import draw_heat_map

def get_text_st(row, labels):
    return labels[int(row["is_text"])]

def draw_pie(group_df, fig, _row, _col):
    labels = ["Посты без текста", "Посты с текстом"]
    group_df["text_info"] = group_df.apply(lambda x: get_text_st(x, labels), axis = 1)
    dif_post_counts = group_df["text_info"].value_counts()
    fig.add_trace(go.Pie(values=dif_post_counts, labels=dif_post_counts.index), row=_row, col=_col)

    
def draw_bar_plot(group_df, fig, row, col, cont_type):
    freq_arr = group_df[cont_type].value_counts()
    fig.add_trace(go.Bar(showlegend=False, x=freq_arr.index, y=freq_arr), row, col)
    fig.update_xaxes(tick0=0, dtick=1, row = row, col = col)    

def draw_table(group_df, fig, row, col):
    group_df["is_photo"] = (group_df["photo_cnt"] != 0).astype(int)
    group_df["is_video"] = (group_df["video_cnt"] != 0).astype(int)

    likes_table_df = get_df_by_stat(group_df, "absol_likes", "Лайк")
    reposts_table_df = get_df_by_stat(group_df, "absol_reposts", "Репост")
    comments_table_df = get_df_by_stat(group_df, "absol_comments", "Комментарий")

    mean_table_df = pd.concat([likes_table_df, reposts_table_df, comments_table_df], ignore_index=True)
    # ru_bool_ind = list(map(lambda ind: dict_bool[ind], mean_table_df.index))
    # print(mean_table_df)

    table = go.Table(
                header=dict(values=["Метрика", "Наличие контента в посте" , "Текст", "Изображение", "Видео"],
                font = dict(color = 'white', size = 13),
                fill_color='royalblue',
                align='left'),
            cells=dict(values=[mean_table_df["statistic"], mean_table_df["is_content"], mean_table_df.is_text_absol_stat,
                mean_table_df.is_photo_absol_stat, mean_table_df.is_video_absol_stat],
               height = 40,
               fill_color = [["paleturquoise","paleturquoise",'rgb(107, 174, 214)',
                                 'rgb(107, 174, 214)',"rgb(49, 130, 189)", 'rgb(49, 130, 189)']],
             font = dict(color = 'black', size = 13),
               align='left'))
    fig.add_trace(table, row, col)   


def get_df_by_stat(group_df, stat, stat_name):
    stat_by_text = get_df_with_mean(group_df, "is_text", stat)
    stat_by_photo = get_df_with_mean(group_df, "is_photo", stat)
    stat_by_video = get_df_with_mean(group_df, "is_video", stat)

    mean_table_df = pd.concat([stat_by_text, stat_by_photo, stat_by_video], axis=1)
    mean_table_df = mean_table_df.round(2)
    mean_table_df["statistic"] = stat_name

    dict_bool = {1 : "Есть", 0: "Нет"}
    mean_table_df["is_content"] = list(map(lambda ind: dict_bool[ind], mean_table_df.index))
    # print(mean_table_df)
    return mean_table_df

def get_df_with_mean(group_df, condition, stat):
    name = condition + '_' + "absol_stat"
    return group_df.groupby(condition).agg({stat: "mean"}).rename(columns={stat:name})


def draw_fig_content(group_df):
    
    fig = make_subplots(rows=2, cols=2, specs=[[{"type": "xy"}, {"type": "domain"}],
                                        [{"type": "xy"}, {"type": "table"}]],
                                        subplot_titles=("Количество постов с изображениями", 
                                        "Наличие текста в посте",
                                        "Количество постов с видео", 
                                        "Мат ожидания основных статистик в зависимости от наличия контента" )) 

    fig.update_layout(autosize=False, width=1400, height=1000, legend_font_size=16)
    draw_pie(group_df, fig, 1, 2)
    draw_bar_plot(group_df, fig, 1, 1, "photo_cnt")
    draw_bar_plot(group_df, fig, 2, 1, "video_cnt")
    draw_table(group_df, fig, 2, 2)

    # fig.add_trace(go.Scatter(x=[4000, 5000, 6000], y=[7000, 8000, 9000]),
    #             row=2, col=2)
    return fig


def draw_kde_by_metrics(src_gr_posts_df, src_gr_title, 
                    cmp_gr_posts_df, cmp_gr_title, metrics):
    start_pos = 0
    step = 0.25
    figs = []
    fig_num = 2
    for metric in metrics:

        figs.append(draw_figure_kde(src_gr_posts_df[metric], src_gr_title,
                                cmp_gr_posts_df[metric], cmp_gr_title, metric,
                                start_pos, start_pos + step, fig_num))
        fig_num+= 1
        start_pos+= step + 0.1
    traces = []
    for trace in figs:
        for sub_trace in trace.data:
            traces.append(sub_trace)
    # traces = list(map(lambda trace: trace.data[1], figs))
    fig = go.Figure()
    fig.add_traces(traces)
    for sub_fig in figs:
        fig.layout.update(sub_fig.layout)
    # fig = ff.create_distplot([src_gr_posts_df["likes_perc"], cmp_gr_posts_df["likes_perc"]],
    #         [src_gr_title, cmp_gr_title], curve_type='kde',
    #          show_rug =False, show_hist=False)
    fig.update_layout(template = 'plotly_dark')
    fig.show()
    
def draw_figure_kde(src_metric, src_gr_title, 
                    cmp_metric, cmp_gr_title, metric_label, y_min, y_max, gr_num):
    legends =  [src_gr_title, cmp_gr_title]
    fig = ff.create_distplot([src_metric, cmp_metric],
            legends, curve_type='kde',
              show_rug =False, show_hist=False)
    # fig.update_layout(template = 'plotly_dark')
    if (gr_num > 2):
        for trace in fig["data"]:
            trace["showlegend"] = False

    gr_num = str(gr_num)
    for i in range(len(fig.data)):
        fig.data[i].xaxis='x' + gr_num
        fig.data[i].yaxis='y' + gr_num
    
    fig['layout']['xaxis' + gr_num]  = {}
    fig['layout']['yaxis' + gr_num] = {}

    # Добавить название
    fig["layout"]["xaxis" + gr_num].update({'anchor': 'y'+ gr_num, "title_text":metric_label})
    fig["layout"]["yaxis" + gr_num].update({'anchor': 'x' + gr_num, 
                    "title_text":"Плотность распределения",  "title_font" :{"size": 10},
                         'domain': [y_min, y_max]})
    fig.update_layout(title_text='Ядерные оценки плотности (KDE)', title_x=0.5)
    # fig["layout"]["title_text"] =  ""
    # print (fig)
    return fig
    