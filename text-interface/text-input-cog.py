import discord
from discord.ext import commands
from database.database_curator import tasksDatabase
from datetime import datetime, date
import asyncio
import os
from database.ics_parser import parse_ics
import math
from datetime import datetime
import pytz

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
            embed.set_footer(text="error; arguments missing")
            await ctx.reply(embed=embed)
            return
        task_title = args[0]
        try:
            task_startdate = datetime.strptime(args[1], '%y/%m/%d-%H:%M')
            if len(args) > 2:
                task_enddate = datetime.strptime(args[2], '%y/%m/%d-%H:%M')
            else:
                task_enddate = task_startdate
        except:
            embed = discord.Embed(color=discord.Colour.brand_red(), title="**s.add 'taskname' startdate enddate**")
            embed.add_field(name="**taskname**", value="str\nThe name of your event\n(must be within quotes)")
            embed.add_field(name="**startdate**", value="YY/MM/DD-HH:SS\nThe start/due date of your task")
            embed.add_field(name="**enddate (opt.)**", value="YY/MM/DD-HH:SS\nThe end date of your task")
            embed.set_footer(text="error; invalid date format")
            await ctx.reply(embed=embed)
            return
        if self._database.get_user(ctx.author.id) is None:
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.add_field(name="You have not registered a timezone, use **s.timezone**", value="")
            await ctx.reply(embed=embed)
            return
        new_task_assert = self._database.add_new_task(ctx.author.id, task_title, task_startdate.timestamp(), task_enddate.timestamp())
        if not new_task_assert:
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.add_field(name=f"Error creating new user with id {ctx.author.id}", value="")
            await ctx.reply(embed=embed)
            return
        #create embed for newly added task
        embed = discord.Embed(color=discord.Colour.brand_red())
        if task_startdate == task_enddate:
            embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Successfully added {task_title}**")
            embed.add_field(name=f"**{task_title}**", value=f"{task_startdate.strftime('%d %b %Y %I:%M%p')}")
            embed.set_footer(text="use s.view to view full schedule.")
            await ctx.reply(embed=embed)
        else:
            embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Successfully added {task_title}**")
            embed.add_field(name=f"**{task_title}**", value=f"{task_startdate.strftime('%d %b %Y %I:%M%p')} to {task_enddate.strftime('%d %b %Y %I:%M%p')}")
            embed.set_footer(text="use s.view to view full schedule.")
            await ctx.reply(embed=embed)

    @commands.command(name="view", aliases=["calendar", "schedule"])
    async def view(self, ctx):
        #list out first 10 tasks
        # just gonna print out the first 10 tasks 
        # Reminder: format is "name", "startdate", "enddate"
        events = self._database.get_user_tasks(ctx.author.id)
        page_size = 10  # define the page size
        num_pages = math.ceil(len(events) / page_size)  # useful for determining bounds of page_number
        page_number = 1  # counting starts at 1, not 0.

        print(events[(page_number-1)*page_size:min(page_number*page_size, len(events))])  # prints out page_size items per page

        # figuring out time stuff

        # first i need to get the user's timezone
        user_info = self._database.get_user(ctx.author.id)
        time_zone = user_info['timezone']
        time_zone = pytz.timezone(time_zone)

        # Step 2: Timezone fuckery
        page_of_events = events[(page_number - 1) * page_size:min(page_number * page_size, len(events))]
        for event in page_of_events:
            name = event['name']
            start_date = event['startdate']  # needs to be converted to local timezone
            end_date = event['enddate']      # needs to be converted to local timezone
            start_date = time_zone.localize(datetime.fromtimestamp(start_date))
            end_date = time_zone.localize(datetime.fromtimestamp(end_date))
            print(f"Name: {name}, Startdate: {str(start_date)}, Enddate: {str(end_date)}")

        # Step 3: Making it look pretty!!
        # -charlie's work

    @commands.command(name="edit", aliases=["postpone"])
    async def edit(self, ctx, *args):
        #s.edit index startdate enddate
        if len(args) != 2 and len(args) != 3:
            embed = discord.Embed(color=discord.Colour.brand_red(), title="**s.edit index startdate enddate**")
            embed.add_field(name="**index**", value="int\nThe index of your event")
            embed.add_field(name="**startdate**", value="YY/MM/DD-HH:SS\nThe new start/due date of your task")
            embed.add_field(name="**enddate (opt.)**", value="YY/MM/DD-HH:SS\nThe new end date of your task")
            embed.set_footer(text="error; missing arguments")
            await ctx.reply(embed=embed)
            return
        index = int(args[0]) - 1
        try:
            task_startdate = datetime.strptime(args[1], '%y/%m/%d-%H:%M')
            if len(args) > 2:
                task_enddate = datetime.strptime(args[2], '%y/%m/%d-%H:%M')
            else:
                task_enddate = task_startdate
        except:
            embed = discord.Embed(color=discord.Colour.brand_red(), title="**s.edit index startdate enddate**")
            embed.add_field(name="**index**", value="int\nThe index of your event")
            embed.add_field(name="**startdate**", value="YY/MM/DD-HH:SS\nThe new start/due date of your task")
            embed.add_field(name="**enddate (opt.)**", value="YY/MM/DD-HH:SS\nThe new end date of your task")
            embed.set_footer(text="error; invalid date format")
            await ctx.reply(embed=embed)
            return
        if self._database.get_user(ctx.author.id) is None:
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.add_field(name="You have not registered a timezone, use **s.timezone**", value="")
            await ctx.reply(embed=embed)
            return
        old_task = self._database.get_user_tasks(ctx.author.id)[index]
        rf_old_task_assert = self._database.remove_task(ctx.author.id, index)
        if not rf_old_task_assert:
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.add_field(name=f"Error removing old task at index {index}", value="")
            await ctx.reply(embed=embed)
            return
        new_task_assert = self._database.add_new_task(ctx.author.id, old_task["name"], task_startdate.timestamp(), task_enddate.timestamp())
        if not new_task_assert:
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.add_field(name=f"Error replacing task at index {index}", value="")
            await ctx.reply(embed=embed)
            return
        #create embed for newly added task
        embed = discord.Embed(color=discord.Colour.brand_red())
        if task_startdate == task_enddate:
            embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Successfully edited {old_task['name']}**")
            embed.add_field(name=f"**{old_task['name']}**", value=f"{task_startdate.strftime('%d %b %Y %I:%M%p')}")
            embed.set_footer(text="use s.view to view full schedule.")
            await ctx.reply(embed=embed)
        else:
            embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Successfully edited {old_task['name']}**")
            embed.add_field(name=f"**{old_task['name']}**", value=f"{task_startdate.strftime('%d %b %Y %I:%M%p')} to {task_enddate.strftime('%d %b %Y %I:%M%p')}")
            embed.set_footer(text="use s.view to view full schedule.")
            await ctx.reply(embed=embed)

    
    @commands.command(name="complete", aliases=["remove", "delete"])
    async def complete(self, ctx, *args):
        if len(args) == 0:
            embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**s.complete index**")
            embed.add_field(name="**index**", value="int\nThe index of the completed task")
            embed.set_footer(text="error; index not given")
            await ctx.reply(embed=embed)
            return
        index = int(args[0]) - 1
        user_tasks = self._database.get_user_tasks(ctx.author.id)
        if index >= 0 and index < len(user_tasks):
            item = user_tasks[index]
            remove_task_assert = self._database.remove_task(ctx.author.id, index)
            if remove_task_assert:
                embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Removed item at index '{index}'**")
                if item['startdate'] == item['enddate']:
                    embed.add_field(name=f"**{item['name']}**", value=f"{date.fromtimestamp(item['startdate']).strftime('%d %b %Y %I:%M%p')}")
                else:
                    embed.add_field(name=f"**{item['name']}**", value=f"{date.fromtimestamp(item['startdate']).strftime('%d %b %Y %I:%M%p')} to {date.fromtimestamp(item['enddate']).strftime('%d %b %Y %I:%M%p')}")
                embed.set_footer(text="use **s.view** to view full schedule.")
                await ctx.reply(embed=embed)
                return
            else:
                embed = discord.Embed(color=discord.Colour.brand_red())
                embed.add_field(name=f"Error removing task at index {index}", value="")
                await ctx.reply(embed=embed)
                return
        else:
            #bad
            embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**s.complete index**")
            embed.add_field(name="**index**", value="int\nThe index of the completed task")
            embed.set_footer(text="error; index out of bounds")
            await ctx.reply(embed=embed)

    @commands.command(name="timezone", aliases=["tz"])
    async def timezone(self, ctx, *args):
        tz = " ".join(args)
        if self._database.get_user(ctx.author.id) is None:
            self._database.add_new_user(ctx.author.id, tz)
        else:
            self._database.edit_user_timezone(ctx.author.id, tz)
        embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Timezone Updated to '{tz}'**")
        embed.add_field(name="You can now add to your schedule with **s.add**", value="")
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
    bot.add_cog(TextInputter(bot))