import discord
from discord.ext.pages import PaginatorButton
import os
import traceback

custom_buttons = [
            PaginatorButton("first", label="<<-", style=discord.ButtonStyle.gray),
            PaginatorButton("prev", label="<-", style=discord.ButtonStyle.gray),
            PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True),
            PaginatorButton("next", label="->", style=discord.ButtonStyle.gray),
            PaginatorButton("last", label="->>", style=discord.ButtonStyle.gray),
        ]
        
def cogs_manager(bot, mode_short, include_root=False):
    cogs_directory = "cogs"
    root_directory = "commands/root_cmds"
    modes = {"l": "load", "u": "unload", "r": "reload"}
    errors = []
    success = []
    mode = modes[mode_short]
    for root, dirs, files in os.walk(cogs_directory):
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), cogs_directory)
            if os.path.dirname(file_path) == root_directory and not include_root:
                print(f"[skipped] {file_path}")
                continue
            if file.endswith(".py"):
                dot_path = f"{cogs_directory}.{file_path[:-3].replace(os.sep, '.')}"
                try:
                    getattr(bot, mode + "_extension")(dot_path)
                    success.append(file_path)
                except Exception as error:
                    traceback.print_exc()
                    errors.append(f"{file_path}: {error}")
    return success, errors, mode


def gawa_embed(style=None, title=None, content=None):
    check_emoji = ""
    cross_emoji = "" # replace mo
    info_emoji = "" 
    if style == None:
        title = info_emoji + (title if title else " info")
        color = None
    elif style == False:
        title = cross_emoji + (title if title else " error")
        color = 0xff6666
    elif style == True:
        title = check_emoji + (title if title else " success")
        color = 0x66ff66
    else:
        raise Exception("ginagawamo")
        
    embed = discord.Embed(title=title,
                          description=f"{content or 'empty'}",
                          color=color)
    return embed
    
class ModifiedDiscordView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.disable_on_timeout = True
        
    async def interaction_check(self, interaction):
        return interaction.user.id == self.ctx.author.id
        
    async def on_check_failure(self, interaction):
        author = self.ctx.author.mention
        embed = gawa_embed(False, None, f"> this interaction is for {author}, not yours")
        await interaction.response.send_message(content=None, embed=embed, ephemeral=True)
        
class ConfirmView(ModifiedDiscordView):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label="confirm", style=discord.ButtonStyle.green)
    async def confirm_callback(self, button, interaction):
        self.style = discord.ButtonStyle.green
        self.children[1].style = discord.ButtonStyle.gray
        self.disable_all_items()
        self.value = True
        self.stop()
        
    @discord.ui.button(label="cancel", style=discord.ButtonStyle.red)
    async def cancel_callback(self, button,  interaction):
        self.style = discord.ButtonStyle.green
        self.children[0].style = discord.ButtonStyle.gray
        self.disable_all_items()
        self.value = False
        self.stop()