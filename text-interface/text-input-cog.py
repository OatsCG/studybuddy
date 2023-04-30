import discord
from discord.ext import commands
from database.database_curator import tasksDatabase
from datetime import datetime
import asyncio
import os

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


class TextInputter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._database = tasksDatabase("tasks.db")

    @commands.command(name="add")
    async def add(self, ctx, *args):
        if len(args) != 2 and len(args) != 3:
            embed = discord.Embed(color=discord.Colour.brand_red(), title="**s.add 'taskname' startdate enddate**")
            embed.add_field(name="**taskname**", value="str\nThe name of your event\n(must be within quotes)")
            embed.add_field(name="**startdate**", value="YY/MM/DD-HH:SS\nThe start/due date of your task")
            embed.add_field(name="**enddate (opt.)**", value="YY/MM/DD-HH:SS\nThe end date of your task")
            embed.set_footer(text="s.add")
            await ctx.reply(embed=embed)
            return
        task_title = args[0]
        try:
            task_startdate = datetime.strptime(args[1], '%y/%m/%d %H:%M')
            task_enddate = datetime.strptime(args[2], '%y/%m/%d %H:%M')
        except:
            embed = discord.Embed(color=discord.Colour.brand_red(), title="**s.add 'taskname' startdate enddate**")
            embed.add_field(name="**taskname**", value="str\nThe name of your event\n(must be within quotes)")
            embed.add_field(name="**startdate**", value="YY/MM/DD-HH:SS\nThe start/due date of your task")
            embed.add_field(name="**enddate (opt.)**", value="YY/MM/DD-HH:SS\nThe end date of your task")
            embed.set_footer(text="s.add")
            await ctx.reply(embed=embed)
            return
        if self._database.get_user(ctx.author.id) is None:
            embed = discord.Embed(color=discord.Colour.blurple())
            embed.add_field(name="You have not registered a timezone, use **s.timezone**")
            await ctx.reply(embed=embed)
            return
        new_task_assert = self._database.add_new_task(ctx.author.id, task_title, task_startdate, task_enddate)
        if not new_task_assert:
            embed = discord.Embed(color=discord.Colour.blurple())
            embed.add_field(name=f"Error creating new user with id {ctx.author.id}")
            await ctx.reply(embed=embed)
            return
        #create embed for newly added task
        embed = discord.Embed(
            title="My Amazing Embed",
            description="Embeds are super easy, barely an inconvenience.",
            color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
        )
        if task_startdate == task_enddate:
            embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Successfully added {task_title}**")
            embed.add_field(name=f"**{task_title}**", value=f"{task_startdate.strftime('%a %d %b %Y %I:%M%p')}")
            embed.set_footer(text="use **s.view** to view full schedule.")
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"**{task_title}** added to schedule from **{task_startdate.strftime('%a %d %b %Y %I:%M%p')}** to {task_enddate.strftime('%a %d %b %Y %I:%M%p')}! use **s.view** to view your schedule.")

    @commands.command(name="view", aliases=["calendar", "schedule"])
    async def view(self, ctx):
        #list out first 10 tasks
        tasks = self._database.get_user_tasks(ctx.author.id)
        page = 0 #IMPLEMENT
        todolist = [tasks[x] for x in range(page*10, min(len(tasks), (page+1)*10))]
        #create embed for viewing tasks
        embed = discord.Embed(
            title="My Amazing Embed",
            description="Embeds are super easy, barely an inconvenience.",
            color=discord.Colour.blurple(), # Pycord provides a class with default colors you can choose from
        )

        for task in todolist:
            embed.add_field(name=task["name"], value=task["startdate"] + " - " + task["enddate"], inline=True)
        
        #embed.set_footer(text="Footer! No markdown here.") # footers can have icons too
        embed.set_author(name=ctx.author.name + "'s Schedule", icon_url=ctx.author.display_avatar)
        embed.set_thumbnail(url="https://example.com/link-to-my-thumbnail.png")
        embed.set_image(url="https://example.com/link-to-my-banner.png")
    
        await ctx.reply(embed=embed)
    
    @commands.command(name="complete", aliases=["remove", "delete"])
    async def complete(self, ctx, channel: discord.TextChannel, text: str):
        #remove task from database
        await channel.send(text)

    @commands.command(name="timezone", aliases=["tz"])
    async def timezone(self, ctx, *args):
        tz = " ".join(args)
        self._database.add_new_user(ctx.author.id, tz)
        embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Timezone Updated to '{tz}'**")
        embed.add_field(name="You can now add to your schedule with **s.add**")
        await ctx.reply(embed=embed)

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

        await ctx.author.send("You have 10 seconds to upload a file.")

        def check(m: discord.Message):
            extensions = [".ical", ".ics", ".ifb", ".icalendar"]
            return m.author.id == ctx.author.id and m.channel.id == ctx.author.dm_channel.id and m.attachments \
                and os.path.splitext(m.attachments[0].filename)[1] in extensions

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=10)
        except asyncio.TimeoutError:
            await ctx.send("You did not respond in time.")
            return
        else:
            await ctx.send(f"You responded with {msg.content}!")
            return

def setup(bot):
    bot.add_cog(TextInputter(bot))