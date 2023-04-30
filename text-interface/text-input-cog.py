import discord
from discord.ext import commands
from database_curator import tasksDatabase
from datetime import datetime


class Basics(commands.Cog):
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
    
    @commands.command(name="upload", aliases=["ics"])
    async def upload(self, ctx, channel: discord.TextChannel, text: str):
        #dm user to prompt for file
        await channel.send(text)
    
    @commands.command(name="complete", aliases=["remove", "delete"])
    async def complete(self, ctx, channel: discord.TextChannel, text: str):
        #remove task from database
        await channel.send(text)

    @commands.command(name="timezone", aliases=["tz"])
    async def timezone(self, ctx, channel: discord.TextChannel, text: str):
        #dm user to prompt for file
        await channel.send(text)


def setup(bot):
    bot.add_cog(Basics(bot))