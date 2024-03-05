import os
import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utensils.discord import cogs_manager
# what he cookin 🥶🍳

os.chdir(os.path.dirname(__file__))

load_dotenv("./storage/.env")
cogs_directory = "cogs"

intents = discord.Intents.all() # 😈
bot = commands.Bot(command_prefix=commands.when_mentioned_or(";"),intents=intents)

results = cogs_manager(bot, "l", True)
for tray in results:
    for cog in tray:
        if cog in results[0]:
            print(f"[200] {cog}")
        elif cog in results[1]:
            print(f"[400] {cog}")

bot.start_time = datetime.datetime.now()
print(f"[start] {os.path.basename(__file__)}")
bot.run(os.getenv("DISCORD_TOKEN"))