import discord
from discord.ext import commands
import os
from utensils.redis import database, admin_list_sync, puwede_ba
from utensils.discord import gawa_embed
import json
    
class ServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=["inv"])
    @puwede_ba()
    async def invite_create(self, ctx, channel: discord.TextChannel = None, time: str = "1m", max_uses: int = 1):
        if not channel:
            channel = ctx.channel
        if "d" in time:
            duration = int(time.split("d")[0]) * 86400
        elif "h" in time:
            duration = int(time.split("h")[0]) * 3600
        elif "m" in time:
            duration = int(time.split("m")[0]) * 60
        elif time.isdigit() or "s" in time:
            time = time.replace("s", "")
            duration = int(time)
        else:
            duration = 60
            
        link = await channel.create_invite(max_age=duration, max_uses=max_uses, unique=True)
        await ctx.send(f"invite info:\n{channel.mention} {time} {max_uses} uses")
        await ctx.send(f"{link}")
        
def setup(bot):
    bot.add_cog(ServerCommands(bot))
