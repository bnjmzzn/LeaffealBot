import discord
from discord.ext import commands
import os
from utensils.discord import cogs_manager, gawa_embed

class OwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=["mc"])
    @commands.is_owner()
    async def manage_cog(self, ctx, mode = "r"):
        success, errors, mode = cogs_manager(self.bot, mode)
        embeds = []
        if success:
            embed = gawa_embed(True, f"{mode}ed cogs", "\n".join(success))
            embeds.append(embed)
        if errors:
            embed = gawa_embed(False, None, "\n".join(errors))
            embeds.append(embed)
        await ctx.send(embeds=embeds)
        
    @commands.command(aliases=["rb"])
    @commands.is_owner()
    async def restart_bot(self, ctx):
        await ctx.send("bot restarting")
        print(f"[restart] {self.bot.user}")
        os.system(f"python utensils/restarter.py {self.bot.user}")
        await self.bot.close()
        
    @commands.command(aliases=["sb"])
    @commands.is_owner()
    async def shutdown_bot(self, ctx):
        await ctx.send("shutting down")
        await self.bot.close()
            
def setup(bot):
    bot.add_cog(OwnerCommands(bot))