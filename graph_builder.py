from random import random
import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import kaleido
import pandas as pd
import numpy as np


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

def draw_heatmap(group_df, fig, row, col):
    z = [[1,4],
     [5,2]]
    
    trace1 = ff.create_annotated_heatmap(z = z,
                                         x = ["Not use","Use"],
                                         y = ["Not use","Use"],
                                         showscale  = False,name = "matrix")
    fig.add_trace(go.Heatmap(trace1.data[0]), 2 ,2)   


def draw_fig_content(group_df):
    
    fig = make_subplots(rows=2, cols=2, specs=[[{"type": "xy"}, {"type": "domain"}],
                                        [{"type": "xy"}, {"type": "Heatmap"}]],
                                        subplot_titles=("Количество постов с изображениями", 
                                        "Наличие текста в посте",
                                        "Количество постов с видео", 
                                        "Мат ожидания основных статистик в зависимости от типа контента" )) 
    # трабл с хит мап  в типе!

    fig.update_layout(autosize=False, width=1400, height=1000, legend_font_size=16)
    draw_pie(group_df, fig, 1, 2)
    draw_bar_plot(group_df, fig, 1, 1, "photo_cnt")
    draw_bar_plot(group_df, fig, 2, 1, "video_cnt")
    draw_heatmap(group_df, fig, 2, 2)

    # fig.add_trace(go.Scatter(x=[4000, 5000, 6000], y=[7000, 8000, 9000]),
    #             row=2, col=2)
    return fig
