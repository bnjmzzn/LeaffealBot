import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, InputText
from utensils.discord import gawa_embed, ModifiedDiscordView
from utensils.redis import database, puwede_ba
import json
from datetime import datetime, timedelta, timezone

class RefreshView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Refresh", custom_id="refresh", style=discord.ButtonStyle.gray)
    async def button_callback(self, button, interaction):
        utc8 = timezone(timedelta(hours=8))
        pending = {
            "today": {},
            "tomorrow": {},
            "soon": {}
        }
        
        quest_ids = database.keys("quest:*")
        pipe = database.pipeline()
        for quest in quest_ids:
            pipe.get(quest)
        quest_values = pipe.execute()
        
        for index, quest_value in enumerate(quest_values):
            quest_data = json.loads(quest_value)
            
            deadline = datetime.strptime(quest_data["deadline"], "%Y%m%d").date()
            today = datetime.now(utc8).date()
            tomorrow = today + timedelta(days=1)
            
            if deadline == today:
                pending["today"][quest_ids[index]] = quest_data
            elif deadline == tomorrow:
                pending["tomorrow"][quest_ids[index]] = quest_data
            elif deadline > tomorrow:
                delta = (deadline - today).days
                pending["soon"][quest_ids[index]] = quest_data
                pending["soon"][quest_ids[index]]["days"] = delta
            else:
                pass
            
        sorted_today = dict(sorted(pending["today"].items(), key=lambda x: x[1]["subject"]))
        sorted_tomorrow = dict(sorted(pending["tomorrow"].items(), key=lambda x: x[1]["subject"]))
        sorted_soon = dict(sorted(pending["soon"].items(), key=lambda x: x[1]["days"]))
        
        pending = {"today": sorted_today, "tomorrow": sorted_tomorrow, "soon": sorted_soon}
        embeds = []
        # loop through today, tomorrow, and soon
        for status in pending.keys():
            # if the status is not empty
            if pending[status]:
                # make an embed for the status
                if status.startswith("today"):
                    embed = discord.Embed(
                        title=f"{status.upper()}",
                        color=0xff7f7f)
                elif status.startswith("tomorrow"):
                    embed = discord.Embed(
                        title=f"{status.upper()}",
                        color=0xffffff)
                else:
                    embed = discord.Embed(
                        title=f"{status.upper()}",
                        color=0x90ee90)
                
                # loop through all quests in a status
                for quest in pending[status].keys():
                    quest_id = str(quest.split(":")[1])
                    
                    content = pending[status][quest]['content']
                    if content.startswith("Check the thread below this message"):
                        content = "Check the thread"
                    
                    # if the quest is under "soon" status, add days remaining
                    if status.startswith("soon"):
                        days = f"in {pending[status][quest]['days']} days"
                        embed.add_field(
                            name=f"{pending[status][quest]['subject']} (ID: {quest_id}) {days}",
                            value=f"{content}",
                            inline=False)
                    else: 
                        embed.add_field(
                            name=f"{pending[status][quest]['subject']} (ID: {quest_id})",
                            value=f"{content}",
                            inline=False)
                embeds.append(embed)
                
        if not embeds:
            embed = discord.Embed(title=f"Wala hooray", color=0xffffff)
            embeds.append(embed)
                
        now = datetime.now(utc8).strftime('%B %d %Y at %I:%M %p')
        edit_content = f"__**REMINDERS!**__\nLast refresh: {now}"
        await self.message.edit(content=edit_content, embeds=embeds, view=self)

class QuestEditorModal(Modal):
    def __init__(self, quest_key, quest_content):
        super().__init__(title=f"editing {quest_key}")
        self.quest_key = quest_key
        self.add_item(InputText(label="content", value=quest_content, style=discord.InputTextStyle.long))
    
    async def callback(self, interaction):
        quest_data_parts = self.children[0].value.split("\n")
        
        message_id = quest_data_parts[0]
        assigned = quest_data_parts[1]
        deadline = quest_data_parts[2]
        subject = quest_data_parts[3].upper()
        content = "\n".join(quest_data_parts[4:])
        
        data = {}
        data["message_id"] = message_id
        data["assigned"] = assigned
        data["deadline"] = deadline
        data["subject"] = subject
        data["content"] = content
        
        data_string = json.dumps(data)
        database.set(self.quest_key, data_string)
        
        assigned_format = datetime.strptime(assigned, "%Y%m%d").strftime("%B %d, %Y")
        deadline_format = datetime.strptime(deadline, "%Y%m%d").strftime("%B %d, %Y")
        subject_format = subject.replace("_"," ").upper()
        
        config_data = json.loads(database.get("cfg:root"))
        channel = await interaction.client.fetch_channel(config_data["quest_channel"])
        message = await channel.fetch_message(message_id)
        
        message_content = f"**ID: {self.quest_key.split(':')[1]}**"
        embed_title = f"{subject_format}:"
        embed_desc = (\
                f"Assigned: {assigned_format}\n" +
                f"Deadline: {deadline_format}\n" +
                f">>> {content}")
        embed = discord.Embed(title=embed_title, description=embed_desc, color=0x90ee90)
        message = await message.edit(content=message_content, embed=embed)
        
        embed = gawa_embed(True, None, f"> `{self.quest_key}` edited")
        await interaction.response.edit_message(content=None, embed=embed, view=None)
        
class EditQuestView(ModifiedDiscordView):
    def __init__(self, ctx, quest_key, quest_content):
        super().__init__()
        self.ctx = ctx
        self.quest_key = quest_key
        self.quest_content = quest_content
        
    @discord.ui.select(
        placeholder = "actions",
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(label="edit"),
            discord.SelectOption(label="cancel")
        ]
    )
    async def select_callback(self, select, interaction):
        if select.values[0] == "edit":
            await interaction.response.send_modal(QuestEditorModal(self.quest_key, self.quest_content))
        elif select.values[0] == "cancel":
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
        
class QuestCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=["qc"])
    @puwede_ba()
    async def quest_create(self, ctx, assigned=".", deadline=".", subject=None, *content):
        
        def convert_date(string_date):
            if string_date == ".":
                string_date = datetime.today().strftime("%Y%m%d")
            else:
                string_date = string_date.replace("/","").replace("-","")
            check = datetime.strptime(string_date, "%Y%m%d")
            return string_date
            
        assigned = convert_date(assigned)
        deadline = convert_date(deadline)
        
        content = " ".join(content) or "Check the thread below this message"
        
        config_data = json.loads(database.get("cfg:root"))
        
        config_data["quest_index"] += 1
        quest_id = config_data["quest_index"]
        quest_prefix = config_data["quest_prefix"]
        quest_key = quest_prefix + str(quest_id)
        
        assigned_format = datetime.strptime(assigned, "%Y%m%d").strftime("%B %d, %Y")
        deadline_format = datetime.strptime(deadline, "%Y%m%d").strftime("%B %d, %Y")
        subject_format = subject.replace("_"," ").upper()
        
        channel = await self.bot.fetch_channel(config_data["quest_channel"])
        message_content = f"**ID: {quest_key.split(':')[1]}**"
        embed_title = f"{subject_format}:"
        embed_desc = (\
                f"Assigned: {assigned_format}\n" +
                f"Deadline: {deadline_format}\n" +
                f">>> {content}")
        embed = discord.Embed(title=embed_title, description=embed_desc, color=0x90ee90)
        message = await channel.send(content=message_content, embed=embed)
        
        if ctx.message.attachments:
            thread = await message.create_thread(name="Attachments", auto_archive_duration=60)
            for attachment in ctx.message.attachments:
                await thread.send(file=await attachment.to_file())
            await thread.archive()
        
        data = {}
        data["message_id"] = message.id
        data["subject"] = subject.upper().replace("_"," ")
        data["assigned"] = assigned
        data["deadline"] = deadline
        data["content"] = content
        
        database.set(quest_key, json.dumps(data))
        database.set("cfg:root", json.dumps(config_data))
        
        embed = gawa_embed(True, None, f"> `{quest_key}` created")
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["qe"])
    @puwede_ba()
    async def quest_edit(self, ctx, quest_key):
        quest_key = "quest:" + quest_key
        quest_data_string = database.get(quest_key)
        if not quest_data_string:
            embed = gawa_embed(False, None, "> quest not found")
            
        quest_data = json.loads(quest_data_string)
        message_id = quest_data["message_id"]
        assigned = quest_data["assigned"]
        deadline = quest_data["deadline"]
        subject = quest_data["subject"]
        content = quest_data["content"]
        
        quest_content = f"{message_id}\n{assigned}\n{deadline}\n{subject}\n{content}"
        
        embed = gawa_embed(None, f"viewing `{quest_key}`", quest_content )
        await ctx.send(embed=embed, view=EditQuestView(ctx, quest_key, quest_content))
        
    @commands.command(aliases=["qd"])
    @puwede_ba()
    async def quest_display(self, ctx):
        await ctx.message.delete()
        await ctx.send("pwease rwefwesh u3u", view=RefreshView(self.bot))
        
def setup(bot):
    bot.add_cog(QuestCommands(bot))
