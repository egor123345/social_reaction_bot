import os
import time
def send_plotly_img_by_bot(file_path, fig, message, bot):
    time.sleep(1)
    fig.write_image(file_path)
    time.sleep(1)
    msg = message
    with open(file_path, 'rb') as graphic:
         msg = bot.send_photo(message.chat.id, photo=graphic)

    if os.path.isfile(file_path):
            os.remove(file_path)
    return msg

