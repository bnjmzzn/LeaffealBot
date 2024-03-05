import discord
from discord.ext import commands
import calendar
from datetime import datetime, timezone, timedelta
from utensils.redis import database
from utensils.discord import gawa_embed
import json

class MonthMenu(discord.ui.Select):
    def __init__(self, month):
        super().__init__()
        self.all_months = list(calendar.month_name)
        
        self.placeholder = self.all_months[month]
        self.min_values = 1
        self.max_values = 1
        self.options = [discord.SelectOption(label=month) for month in self.all_months[1:]]
        
    async def callback(self, interaction):
        self.view.month = int(self.all_months.index(self.values[0]))
        
        content = calendar.month(self.view.year, self.view.month)
        view = CalendarView(self.view.month, self.view.year)
        await interaction.response.edit_message(content=f"```{content}```", view=view)
        
class YearMenu(discord.ui.Select):
    def __init__(self, year):
        super().__init__()
        self.years = list(range(year - 5, year + 6))
        
        self.placeholder = str(year)
        self.min_values = 1
        self.max_values = 1
        self.options = [discord.SelectOption(label=str(year)) for year in self.years]
        self.options[5].description = "current selected"
        
    async def callback(self, interaction):
        self.view.year = int(self.values[0])
        
        content = calendar.month(self.view.year, self.view.month)
        view = CalendarView(self.view.month, self.view.year)
        await interaction.response.edit_message(content=f"```{content}```", view=view)
        
class CalendarView(discord.ui.View):
    def __init__(self, month, year):
        super().__init__()
        self.month = month
        self.year = year
        self.add_item(MonthMenu(self.month))
        self.add_item(YearMenu(self.year))
        self.disable_on_timeout = True

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        calendar.setfirstweekday(calendar.SUNDAY)
    
    @commands.command(aliases=["c"])
    async def calendar(self, ctx, month = None, year = None):
        month = int(month or 0) or datetime.today().month
        year = int(year or 0) or datetime.today().year
        content = calendar.month(year, month)
        view = CalendarView(month, year)
        await ctx.send(f"```{content}```", view=view)
        
    @commands.command(aliases=["z"])
    async def log_template(self, ctx, date, *subjects):
        utc8 = timezone(timedelta(hours=8))
        subjects = list(subjects)
        
        if date == ".":
            time = datetime.now(utc8).replace(hour=12, minute=00, second=00, microsecond=00)
        else:
            time = date.replace("/","").replace("-","")
            time = datetime.strptime(time, "%Y%m%d").replace(tzinfo=utc8)
        timestamp = int(time.timestamp())
        timestamp_string = f"<t:{timestamp}:F>"
        
        content = [timestamp_string]
        
        if not subjects:
            data = database.get("cfg:subjects")
            data = json.loads(data)
            if not data:
                data = '{"mon":[],"tue":[],"wed":[],"thu":[],"fri":[]}'
                database.set("cfg:subjects", data)
                embed = gawa_embed(False, None, "> no subjects template found")
                await ctx.send(embed=embed)
                return
            
            current_weekday = time.weekday()
            print(current_weekday)
            if 0 <= current_weekday <= 4:
                for subject in data[list(data.keys())[current_weekday]]:
                    subjects.append(subject)
            
        for subject in subjects:
            subject = subject.replace("_"," ")
            subject = subject.upper()
            content.append(f"> __**{subject}**__")
            content.append(f"> Lesson: ")
            content.append("> \n> ")
            content.append(f"> Activity: ")
            content.append("> \n> ")
            content.append(f"> Assignments: ")
            content.append("> \n> ")
            content.append(f"\n")
        
        content.append("Dismissal: ")
        
        content = "\n".join(content)
        await ctx.send(f"```{content}```")
        
def setup(bot):
    bot.add_cog(Utilities(bot))
