import requests
import config

VK_TOKEN = config.HASH

def get_vk_groups_info(message):
    start_index = (message.text).rfind('/') + 1
    gr_domain = (message.text)[start_index :]
    gr_name_par = {
                'access_token': VK_TOKEN,
                'v':5.131,
                "screen_name": gr_domain}
    owner_id = requests.get('https://api.vk.com/method/utils.resolveScreenName', gr_name_par).json()
    if (len(owner_id["response"]) == 0):
        raise Exception("Не удалось получить данные о группе Vk")

    input_type = owner_id["response"]["type"]
    owner_id = owner_id["response"]["object_id"]
    if (input_type == "group"):
        owner_id*= -1

    params={
                'access_token': VK_TOKEN,
                'v':5.131,
                "owner_id": owner_id,
                "count": 100 
    }

    gr_posts = requests.get('https://api.vk.com/method/wall.get', params=params)
    gr_posts_info = gr_posts.json()
    if ("error" in gr_posts_info): 
        raise Exception("Не удалось получить данные о группе Vk")
    gr_posts = gr_posts_info["response"]['items']
    if (len(gr_posts) == 0):
        raise Exception("Не удалось получить данные о группе Vk")
    if ("is_pinned" in gr_posts[0] and gr_posts[0]["is_pinned"] == True):
        gr_posts.pop(0)
    for i, post in enumerate(gr_posts):
        gr_posts[i]["likes_perc"] = post["likes"]["count"] / post["views"]["count"] * 100
        gr_posts[i]["reposts_perc"] = post["reposts"]["count"] / post["views"]["count"] * 100
        gr_posts[i]["comments_perc"] = post["comments"]["count"] / post["views"]["count"] * 100

    add_el_to_arr_dict(gr_posts, "likes", "absol_likes")
    add_el_to_arr_dict(gr_posts, "reposts", "absol_reposts")
    add_el_to_arr_dict(gr_posts, "comments", "absol_comments")
    return gr_posts


def add_el_to_arr_dict(gr_posts, el, el_name):
    for dict in gr_posts:
        dict[el_name] = dict[el]["count"]