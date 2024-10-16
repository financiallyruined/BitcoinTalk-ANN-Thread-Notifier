import telebot
import requests
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query
import threading
import time
from config import *

BITCOINTALK_ANN_URL = "https://bitcointalk.org/index.php?board=159.0;sort=first_post;desc"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
}


db = TinyDB('ann_threads.json')
chat_ids_table = db.table('chat_ids')
new_threads_table = db.table('new_threads')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    if not chat_ids_table.contains(Query().chat_id == chat_id):
        chat_ids_table.insert({'chat_id': chat_id})
        bot.reply_to(message, f"Welcome! Your chat ID ({chat_id}) has been registered.")
    else:
        bot.reply_to(message, f"Welcome back! Your chat ID ({chat_id}) is already registered.")

def check_new_threads():
    try:
        r = requests.get(BITCOINTALK_ANN_URL, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        new_threads = soup.select('span[id^="msg"]')[6:]  # exclude the pinned messages
        new_threads_info = [(row["id"], row.find("a")["href"], row.text) for row in new_threads][::-1]  # reverse to make latest thread last

        print("Checking for new threads. Will send notification if found...")

        existing_ids = [thread['msg_id'] for thread in new_threads_table.all()]
        chat_ids = [chat['chat_id'] for chat in chat_ids_table.all()]

        for thread in new_threads_info:
            if thread[0] not in existing_ids:
                print(f"{thread[1]} - {thread[2]}")
                for chat_id in chat_ids:
                    bot.send_message(chat_id, f"{thread[1]} - {thread[2]}")

        #new_threads_table.truncate()  # Clear the table
        new_threads_table.insert_multiple([{'msg_id': t[0], 'link': t[1], 'thread_topic': t[2]} for t in new_threads_info])

    except Exception as e:
        print(f"error: {e}")

def main():
    while True:
        check_new_threads()
        time.sleep(TIME_INTERVAL * 60) #converted to seconds

if __name__ == "__main__":
    main_thread = threading.Thread(target=main)
    main_thread.daemon = True
    main_thread.start()

    bot.polling()
