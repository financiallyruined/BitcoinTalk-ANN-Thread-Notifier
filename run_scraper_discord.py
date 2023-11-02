import discord
import requests
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import sqlite3
from config import *


BITCOINTALK_ANN_URL = "https://bitcointalk.org/index.php?board=159.0;sort=first_post;desc"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
}

conn = sqlite3.connect("ann_threads.db")
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS new_threads (
        msg_id TEXT PRIMARY KEY,
        link TEXT,
        thread_topic TEXT
    )
"""
)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Discord bot connected as {bot.user.name}")
    check_new_threads.start()


@tasks.loop(minutes=TIME_INTERVAL)
async def check_new_threads():
    try:
        r = requests.get(BITCOINTALK_ANN_URL, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        # new_threads = soup.find_all("span", id=lambda value: value and value.startswith("msg"))[6:]
        new_threads = soup.select('span[id^="msg"]')[6:]  # exclude the pinned messages
        new_threads_info = [(row["id"], row.find("a")["href"], row.text) for row in new_threads][::-1] # reverse to make latest thread last

        print("Checking for new threads. Will send notification if found...")

        # print(new_threads_info)

        cursor.execute("SELECT msg_id FROM new_threads")
        existing_ids = [id[0] for id in cursor.fetchall()]
        channel = bot.get_channel(CHANNEL_ID)

        for thread in new_threads_info:
            if thread[0] not in existing_ids:
                print(f"{thread[1]} - {thread[2]}")
                await channel.send(f"{thread[1]} - {thread[2]}")

        cursor.execute("DELETE FROM new_threads")
        cursor.executemany(
            "INSERT INTO new_threads (msg_id, link, thread_topic) VALUES (?, ?, ?)",
            new_threads_info,
        )
        conn.commit()

    except Exception as e:
        print(f"error: {e}")


bot.run(BOT_TOKEN)
