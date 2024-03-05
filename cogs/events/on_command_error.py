import discord
from discord.ext import commands
from utensils.discord import gawa_embed
from utensils.redis import database
import traceback

class on_command_error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            embed = gawa_embed(False, None, "> you are not allowed to use this command")
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandNotFound):
            embed = gawa_embed(False, None, f"> `{ctx.invoked_with}` not found")
            await ctx.send(embed=embed)
        else:
            global traceback_string
            embed = gawa_embed(False, None, f"> syntax:\n> `{ctx.prefix}{ctx.command} {ctx.command.signature}`")
            await ctx.send(embed=embed)
            traceback_string = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            database.set("cfg:trace", traceback_string)
        
    
def setup(bot):
    bot.add_cog(on_command_error(bot))