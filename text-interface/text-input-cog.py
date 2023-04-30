import discord
from discord.ext import commands
from database.database_curator import tasksDatabase
import asyncio
import os
from database.ics_parser import parse_ics

class MyModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Short Input"))
        self.add_item(discord.ui.InputText(label="Long Input", style=discord.InputTextStyle.long))

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Modal Results")
        embed.add_field(name="Short Input", value=self.children[0].value)
        embed.add_field(name="Long Input", value=self.children[1].value)
        await interaction.response.send_message(embeds=[embed])

class MyView(discord.ui.View):
    @discord.ui.button(label="Send Modal")
    async def button_callback(self, button, interaction):
        await interaction.response.send_modal(MyModal(title="Modal via Button"))


class Basics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._database = tasksDatabase("tasks.db")

    @commands.command(name="add")
    async def add(self, ctx: commands.Context):
        await ctx.send(view=MyView())

        #if self._database.get_user(ctx.author.id) is None:
            #await ctx.send("Hello!")
    
    @commands.command(name="view", aliases=["calendar", "schedule"])
    async def view(self, ctx, text: str):
        #list out first 10 tasks
        await ctx.send(text)
    
    @commands.command(name="upload", aliases=["ics"])
    async def upload(self, ctx, channel: discord.TextChannel, text: str):
        #dm user to prompt for file
        await channel.send(text)
    
    @commands.command(name="complete", aliases=["remove", "delete"])
    async def complete(self, ctx, channel: discord.TextChannel, text: str):
        #remove task from database
        await channel.send(text)

    @commands.command(name="file", aliases=["fromfile"])
    async def file(self, ctx):
        # need to check if timezone exists; if not, the user cannot run this command
        # user_data = self._database.get_user(ctx.author.id)
        # if not user_data:
        #     await ctx.send("You don't have a timezone!!")
        #     return
        # elif "timezone" not in user_data:
        #     await ctx.send("You don't have a timezone!!")
        #     return

        await ctx.author.send("You have 30 seconds to upload a file.")

        def check(m: discord.Message):
            extensions = [".ical", ".ics", ".ifb", ".icalendar"]
            return m.author.id == ctx.author.id and m.channel.id == ctx.author.dm_channel.id and m.attachments \
                and os.path.splitext(m.attachments[0].filename)[1] in extensions

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("You did not respond in time.")
            return
        else:

            msg_content = await msg.attachments[0].read()
            ics_parsed = parse_ics(msg_content)
            for event in ics_parsed:
                self._database.add_new_task(ctx.author.id, event["Name"], event["Start time"], event["End time"])
            
            await ctx.send("Calendar information has been parsed successfully.")
            return


        


def setup(bot):
    bot.add_cog(Basics(bot))