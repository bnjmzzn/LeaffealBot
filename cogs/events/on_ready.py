import discord
from discord.ext import commands, tasks
from cogs.commands.quest.quest import RefreshView
from utensils.redis import database, admin_list_sync
import random
import json

class on_ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @tasks.loop(seconds=60*60)
    async def status_changer(self):
        data = database.get("cfg:status")
        
        if not data:
            data = '{"choices":["pls lang"]}'
            database.set("cfg:status", data)
        
        choices = json.loads(data)["choices"]
        state = random.choice(choices)
        await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.custom,
                    name="Custom Status",
                    state=state,
                ),
                status=discord.Status.dnd
        )
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[on_ready] {self.bot.user}')
        self.status_changer.start()
        await self.bot.sync_commands()
        self.bot.add_view(RefreshView(self.bot))
        admin_list_sync()
    
def setup(bot):
    bot.add_cog(on_ready(bot))