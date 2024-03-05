import discord
from discord.ext import commands
from discord.ext.pages import Paginator, Page
from discord.ui import View, Select, Modal, InputText
from utensils.redis import database, puwede_ba
from utensils.discord import custom_buttons, gawa_embed, ConfirmView, ModifiedDiscordView
import json
import os

class KeyEditorModal(Modal):
    def __init__(self, view, key):
        super().__init__(title = f"editing {key[0]}")
        self.view = view
        self.add_item(InputText(label="key name", value=key[0]))
        self.add_item(InputText(label="content", value=key[1], style=discord.InputTextStyle.long))
    
    async def callback(self, interaction):
        key_name = self.children[0].value
        key_value = self.children[1].value
        
        try:
            json_test = json.loads(key_value)
        except Exception as error:
            embed = gawa_embed(False, "invalid json!", error)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        database.set(key_name, key_value)
        
        embed = gawa_embed(True, f"`{key_name}` edited", f"\n```json\n{key_value}```")
        await interaction.response.edit_message(embed=embed, view=ToolView(self.view.ctx, key_name, key_value))

class ToolView(ModifiedDiscordView):
    def __init__(self, ctx, *key: tuple): # key_name, key_value
        super().__init__()
        self.ctx = ctx
        self.key = key
        
    @discord.ui.select(
        placeholder = "actions",
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(label="edit"),
            discord.SelectOption(label="delete")
        ]
    )
    async def select_callback(self, select, interaction):
        if select.values[0] == "edit":
            await interaction.response.send_modal(KeyEditorModal(self, self.key))
        elif select.values[0] == "delete":
            content = f"delete `{self.key[0]}` ?"
            view = ConfirmView(self.ctx)
            await interaction.response.send_message(content=content, view=view)
            await view.wait()
            
            if view.value is None:
                await interaction.edit_original_response(view=view)
            elif view.value:
                database.delete(self.key[0])
                
                embed = gawa_embed(None, None, "> ```entry deleted```")
                self.disable_all_items()
                await self.message.edit(content=None, embed=embed, view=self)
                await interaction.edit_original_response(view=view)
            else:
                await interaction.edit_original_response(view=view)

class SelectKeysMenu(Select):
    def __init__(self, keys_list):
        super().__init__(
            placeholder="select a key",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=key) for key in keys_list]
        )
    
    async def callback(self, interaction):
        key_name = self.values[0]
        key_value = database.get(key_name)
        key_value = json.dumps(json.loads(key_value), indent=4)
        embed = gawa_embed(None, key_name, f"```json\n{key_value}```")
        view = ToolView(self.view.ctx, key_name, key_value)
        await interaction.message.edit(content=None, embed=embed, view=view)
        
        
class SelectKeysView(ModifiedDiscordView):
    def __init__(self, ctx, keys_list):
        super().__init__()
        self.ctx = ctx
        self.add_item(SelectKeysMenu(keys_list))
        
class DatabaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=["dbv"])
    @puwede_ba()
    async def database_view(self, ctx, specific_key = None):
        
        if specific_key:
            key_value_no_indent = database.get(specific_key)
            key_value = json.dumps(json.loads(key_value_no_indent), indent=4)
            if not key_value:
                embed = gawa_embed(False, None, f"> {specific_key} not found")
                await ctx.send(embed=embed)
                return
            else:
                embed = gawa_embed(None, specific_key, f"```json\n{key_value}```")
                view = ToolView(ctx, specific_key, key_value)
                await ctx.send(embed=embed, view=view)
                return
        
        if not database.keys():
            embed = gawa_embed(False, None, "> database is empty")
            await ctx.send(embed=embed)
            return
        
        all_keys = sorted([key for key in database.keys()])
        chunked_keys = [all_keys[i:i + 10] for i in range(0, len(all_keys), 10)]
        pages = []
        for keys_list in chunked_keys:
            content = "\n".join(keys_list)
            # create a Page object with custom view for select menu 
            # select menu options depend on the content of the page
            # nakakalito kasi
            custom_view = SelectKeysView(ctx, keys_list)
            page = Page(content=f"```\n{content}```", custom_view=custom_view)
            pages.append(page)
            
        paginator = Paginator(
                        show_indicator=True,
                        use_default_buttons=False,
                        custom_buttons=custom_buttons,
                        pages=pages)
        paginator.ctx = ctx
        await paginator.send(ctx)
        
    @commands.command(aliases=["dbf"])
    @puwede_ba()
    async def database_flush(self, ctx):
        view = ConfirmView(ctx)
        message = await ctx.send("flush database?", view=view)
        await view.wait()
        if view.value is None:
            await message.edit("cancelled", view=view)
        elif view.value:
            database.flushall()
            await message.edit("flushed", view=view)
        else:
            await message.edit("cancelled", view=view)
            
    @commands.command(aliases=["dbx"])
    @puwede_ba()
    async def database_export(self, ctx):
        message = await ctx.send(":fondue: cooking... ")
        data = {}
        keys = sorted(database.keys())
        pipe = database.pipeline()
        for key in keys:
            pipe.get(key)
        result = pipe.execute()
        for index, key in enumerate(keys):
            try:
                data[key] = json.loads(result[index])
            except Exception as error:
                print(result[index], error)
        with open("storage/database.json", "w") as file:
            file.write(json.dumps(data, indent=4))
        with open("storage/database.json", "rb") as file:
            await message.edit(":ramen: file cooked:", file=discord.File(file, "db.json"))
        os.remove("storage/database.json")
        
def setup(bot):
    bot.add_cog(DatabaseCommands(bot))
