import discord
from discord.ext import commands
import datetime
import psutil
from utensils.redis import database
from utensils.discord import gawa_embed
import time

class CustomHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        prefix = self.context.clean_prefix
        cmd_name = command.qualified_name
        cmd_args = command.signature.replace("[","`<").replace("]",">`").replace("<","`<").replace(">",">`")
        if cmd_aliases := command.aliases:
            aliases = "/".join(command.aliases)
            cmd_aliases = f"(`{aliases}`)"
        return f"> {prefix}{cmd_name} {cmd_aliases} {cmd_args}"

    async def send_bot_help(self, mapping):
        embed = gawa_embed(None, "help", "> commands you can use:")

        for cog, commands in mapping.items():
           filtered = await self.filter_commands(commands, sort=True)
           command_signatures = [self.get_command_signature(c) for c in filtered]

           if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)
    
    async def send_command_help(self, command):
        embed = gawa_embed(None, self.get_command_signature(command))
        if command.help:
            embed.description = command.help
        if alias := command.aliases:
            alias = f"`{alias}`"
            embed.add_field(name="aliases:", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.help_command = CustomHelp()
        
    @commands.command(aliases=["ss"])
    async def stats(self, ctx):
        
        def get_redis_latency():
            start_time = time.time()
            database.ping()
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            return latency
        
        delta = datetime.datetime.now() - self.bot.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_format = f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        bot_latency = round(self.bot.latency * 1000, 2)
        redis_latency = round(get_redis_latency(), 2)
        
        try:
            cpu_usage = str(psutil.cpu_percent()) + "%"
        except:
            cpu_usage = "ERROR"
        try:
            ram_usage = str(psutil.virtual_memory().percent) + "%"
        except:
            ram_usage = "ERROR"
        
        content = (f"Uptime - `{uptime_format}`\n" +
                   f"Bot ping: `{bot_latency}ms`\n" +
                   f"Redis ping: `{redis_latency}ms`\n"
                   f"CPU usage: `{cpu_usage}`\n" +
                   f"RAM usage: `{ram_usage}`\n" +
                   f"Version: `2.1`")
        embed = gawa_embed(None, "stats", content)
        await ctx.send(embed=embed)
        
    @commands.command(aliases=["i","src"])
    async def info(self, ctx):
        await ctx.send("?")
        
def setup(bot):
    bot.add_cog(Info(bot))
