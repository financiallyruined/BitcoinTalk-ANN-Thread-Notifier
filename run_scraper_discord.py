import discord
import requests
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import sqlite3
from config import *


conn = sqlite3.connect("bitcointalk_posts.db")
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS new_posts (
        msg_id TEXT PRIMARY KEY,
        link TEXT,
        post_topic TEXT
    )
"""
)


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

BITCOINTALK_URL = "https://bitcointalk.org/index.php?board=159.0"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
}


@bot.event
async def on_ready():
    print(f"Discord bot connected as {bot.user.name}")
    check_new_posts.start()


@tasks.loop(minutes=TIME_INTERVAL)
async def check_new_posts():
    try:
        r = requests.get(BITCOINTALK_URL, headers=headers)

        soup = BeautifulSoup(r.text, "html.parser")

        # new_posts = soup.find_all("span", id=lambda value: value and value.startswith("msg"))[
        #     6:
        # ]

        new_posts = soup.select('span[id^="msg"]')[6:]  # exclude the pinned messages
        new_posts_info = [
            (row["id"], row.find("a")["href"], row.text) for row in new_posts
        ]

        print("Checking for new posts. Will send notification if found...")

        # print(new_posts_info)

        cursor.execute("SELECT msg_id FROM new_posts")
        existing_ids = [id[0] for id in cursor.fetchall()]

        channel = bot.get_channel(CHANNEL_ID)

        for post in new_posts_info:
            if post[0] not in existing_ids:
                print(f"{post[1]} - {post[2]}")
                await channel.send(f"{post[1]} - {post[2]}")

        cursor.execute("DELETE FROM new_posts")

        cursor.executemany(
            "INSERT INTO new_posts (msg_id, link, post_topic) VALUES (?, ?, ?)",
            new_posts_info,
        )

        conn.commit()

    except Exception as e:
        print(f"error: {e}")


bot.run(BOT_TOKEN)
