import discord
from discord.ext import commands
import os
from utensils.redis import database, admin_list_sync, puwede_ba
from utensils.discord import gawa_embed
import json
    
class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=["cfg"])
    @puwede_ba()
    async def config(self, ctx):
        config_data = database.get("cfg:root")
        if not config_data:
            data = {
                "quest_masters": [int(ctx.author.id)],
                "quest_prefix": "quest:",
                "quest_channel": 0,
                "quest_index": 0
            }
            json_string = json.dumps(data)
            database.set("cfg:root", json_string)
        database_command = self.bot.get_command("database_view")
        await ctx.invoke(database_command, specific_key="cfg:root")
        
    @commands.command(aliases=["sa"])
    @puwede_ba()
    async def sync_admin(self, ctx):
        admins = admin_list_sync()
        content = []
        for admin in admins:
            user = await self.bot.fetch_user(admin)
            content.append(f"{user.name} (`{user.id}`)")
        content = "\n".join(content)
        title = "list of admins"
        embed = gawa_embed(True, title, content)
        await ctx.send(embed=embed)
        
    @commands.command(aliases=["pt"])
    @puwede_ba()
    async def send_last_traceback(self, ctx):
        traceback_string = database.get("cfg:trace")
        if not traceback_string:
            traceback_string = "None"
        chunklength = 2000-6
        chunks = [traceback_string[i:i+chunklength ] for i in range(0, len(traceback_string), chunklength )]
        for part in chunks:
            await ctx.send(f"```{part}```")

        
def setup(bot):
    bot.add_cog(Config(bot))
