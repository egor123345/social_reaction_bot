import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
   

def draw_heat_map(group_df, usr_id):
    stat_df = pd.concat([group_df["absol_likes"],
              group_df["absol_reposts"],
              group_df["absol_comments"]], 
              axis=1,
              keys=['Лайк','Репост', 'Комментарий'])
    # print(stat_df)
    h_map = sns.heatmap(stat_df.corr(), annot = True, cmap= 'coolwarm')
    fig = h_map.get_figure()
    path = f"graphs/heat_map_{usr_id}.png"
    fig.suptitle("Корреляция  между лайками, репостами и комментариями")
    fig.savefig(path)
    plt.close(fig)
    return path
