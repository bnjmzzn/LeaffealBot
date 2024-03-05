import redis
import os
from discord.ext import commands
import json

database = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
    )

admin_list = []

def admin_list_sync():
    global admin_list
    config_data = database.get("cfg:root")
    if not config_data:
        print("[400] admin_list_sync: config data not found")
        return
    admin_list = json.loads(config_data)["quest_masters"]
    print(f"[200] admin_list_sync: {admin_list}")
    return admin_list
    
def puwede_ba():
    async def ritemed(ctx):
        app_info = await ctx.bot.application_info()
        owner_id = app_info.owner.id
        author_id = ctx.author.id
        if (author_id in admin_list) or (author_id == owner_id):
            return True
        else:
            return False
    return commands.check(ritemed)