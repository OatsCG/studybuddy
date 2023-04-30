import discord
from discord.ext import commands, tasks
from database.database_curator import tasksDatabase
from datetime import datetime, date, timedelta
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
        self.ping_users.start()

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

        if self._database.get_user(ctx.author.id) is None:
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.add_field(name="You have not registered a timezone, use **s.timezone**", value="")
            await ctx.reply(embed=embed)
            return

        events = self._database.get_user_tasks(ctx.author.id)
        page_size = 10  # define the page size
        num_pages = math.ceil(len(events) / page_size)  # useful for determining bounds of page_number
        page_number = 1  # counting starts at 1, not 0.

        # figuring out time stuff

        # first i need to get the user's timezone
        user_info = self._database.get_user(ctx.author.id)
        time_zone = user_info['timezone']
        time_zone = pytz.timezone(time_zone)

        # Step 3: Making it look pretty!!
        embed = discord.Embed(color=discord.Colour.brand_red())
        embed.set_author(name=f"{ctx.author.name}'s Calendar", icon_url=ctx.author.avatar.url)  # author
        embed.set_footer(text=f"Displaying {(page_number - 1) * 10 + 1} to {min((page_number) * 10, len(events))} of {len(events)}")
        # creating fields for each event
        page_of_events = events[(page_number - 1) * page_size:min(page_number * page_size, len(events))]
        for i, event in enumerate(page_of_events):
            name = event['name']
            start_date = event['startdate']  # needs to be converted to local timezone
            end_date = event['enddate']      # needs to be converted to local timezone
            start_date = time_zone.localize(datetime.fromtimestamp(start_date))
            end_date = time_zone.localize(datetime.fromtimestamp(end_date))
            if start_date != end_date:
                field_value = f"Start date: {start_date.strftime('%b %e %Y @ %k:%M')}\nEnd date: {end_date.strftime('%b %e %Y @ %k:%M')}"
            else:
                field_value = f"Due date: {start_date.strftime('%b %e %Y @ %k:%M')}"
            embed.add_field(
                name=f"{(page_number - 1) * 10 + i + 1}) {name}",
                value=field_value,
                inline=False
            )

        # now i need to add the buttons
        class MyView(discord.ui.View):

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.danger)
            async def on_prev(self, button, interaction):

                embed = interaction.message.embeds[0]
                old_page_number = max(math.ceil(int(embed.footer.text.split(' ')[1]) / 10) - 1, 1)

                page_of_events = events[(old_page_number - 1) * page_size:min(old_page_number * page_size, len(events))]
                new_embed = discord.Embed(color=discord.Colour.brand_red())
                new_embed.set_author(name=embed.author.name, icon_url=embed.author.url)
                new_embed.set_footer(text=f"Displaying {(old_page_number - 1) * 10 + 1} to {min((old_page_number) * 10, len(events))} of {len(events)}")
                for i, event in enumerate(page_of_events):
                    name = event['name']
                    start_date = event['startdate']  # needs to be converted to local timezone
                    end_date = event['enddate']      # needs to be converted to local timezone
                    start_date = time_zone.localize(datetime.fromtimestamp(start_date))
                    end_date = time_zone.localize(datetime.fromtimestamp(end_date))
                    if start_date != end_date:
                        field_value = f"Start date: {start_date.strftime('%b %e %Y @ %k:%M')}\nEnd date: {end_date.strftime('%b %e %Y @ %k:%M')}"
                    else:
                        field_value = f"Due date: {start_date.strftime('%b %e %Y @ %k:%M')}"
                    new_embed.add_field(
                        name=f"{(old_page_number - 1) * 10 + i + 1}) {name}",
                        value=field_value,
                        inline=False
                    )
                await interaction.response.edit_message(view=self, embed=new_embed)

            @discord.ui.button(label="Next", style=discord.ButtonStyle.success)
            async def on_next(self, button, interaction):
                embed = interaction.message.embeds[0]

                old_page_number = min(math.ceil(int(embed.footer.text.split(' ')[1]) / 10) + 1, num_pages)

                page_of_events = events[(old_page_number - 1) * page_size:min(old_page_number * page_size, len(events))]
                new_embed = discord.Embed(color=discord.Colour.brand_red())
                new_embed.set_author(name=embed.author.name, icon_url=embed.author.url)
                new_embed.set_footer(text=f"Displaying {(old_page_number - 1) * 10 + 1} to {min((old_page_number) * 10, len(events))} of {len(events)}")
                for i, event in enumerate(page_of_events):
                    name = event['name']
                    start_date = event['startdate']  # needs to be converted to local timezone
                    end_date = event['enddate']      # needs to be converted to local timezone
                    start_date = time_zone.localize(datetime.fromtimestamp(start_date))
                    end_date = time_zone.localize(datetime.fromtimestamp(end_date))
                    if start_date != end_date:
                        field_value = f"Start date: {start_date.strftime('%b %e %Y @ %k:%M')}\nEnd date: {end_date.strftime('%b %e %Y @ %k:%M')}"
                    else:
                        field_value = f"Due date: {start_date.strftime('%b %e %Y @ %k:%M')}"
                    new_embed.add_field(
                        name=f"{(old_page_number - 1) * 10 + i + 1}) {name}",
                        value=field_value,
                        inline=False
                    )

                embed = new_embed
                await interaction.response.edit_message(view=self, embed=embed)

        await ctx.send(embed=embed, view=MyView())


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
        if tz not in pytz.all_timezones:
            embed = discord.Embed(color=discord.Colour.brand_red(), title=f"**Invalid timezone!!**")
            embed.add_field(name="Please provide a valid tz-name for your timezone.", value="")
            await ctx.reply(embed=embed)
            return
        elif self._database.get_user(ctx.author.id) is None:
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
        
    @tasks.loop(minutes=30)
    async def ping_users(self):
        users = self._database._get_all_users()
        for user in users:
            time_zone = user["timezone"]
            time_zone = pytz.timezone(time_zone)
            assignments = self._database.get_user_tasks(user["discordID"])
            if len(assignments) >= 1:
                assignment = assignments[0]
                # need to convert to user's timezone
                start_date = time_zone.localize(datetime.fromtimestamp(assignment["startdate"]))
                
                if start_date < datetime.now(tz=time_zone):
                    self._database.remove_task(user["discordID"], 0)
                    continue
                if start_date < (datetime.now(tz=time_zone) + timedelta(hours=1, minutes=30)):
                    username = self.bot.get_user(int(user["discordID"]))
                    await username.send(f"Your assignment {assignment['name']} is due in {(start_date - datetime.now(tz=time_zone)).seconds // 60} minutes!")

            if len(assignments) >= 2:
                assignment = assignments[1]
                # need to convert to user's timezone
                start_date = time_zone.localize(datetime.fromtimestamp(assignment["startdate"]))
                
                if start_date < datetime.now(tz=time_zone):
                    self._database.remove_task(user["discordID"], 1)
                if start_date < (datetime.now(tz=time_zone) + timedelta(hours=1, minutes=30)):
                    username = self.bot.get_user(int(user["discordID"]))
                    await username.send(f"Your assignment {assignment['name']} is due in {(start_date - datetime.now(tz=time_zone)).seconds // 60} minutes!")

            if len(assignments) >= 3:
                assignment = assignments[2]
                # need to convert to user's timezone
                start_date = time_zone.localize(datetime.fromtimestamp(assignment["startdate"]))
                
                if start_date < datetime.now(tz=time_zone):
                    self._database.remove_task(user["discordID"], 2)
                if start_date < (datetime.now(tz=time_zone) + timedelta(hours=1, minutes=30)):
                    username = self.bot.get_user(int(user["discordID"]))
                    await username.send(f"Your assignment {assignment['name']} is due in {(start_date - datetime.now(tz=time_zone)).seconds // 60} minutes!")
            
    @commands.command(name="help")
    async def help(self, ctx):
        embed = discord.Embed(color=discord.Colour.brand_red())
        embed.set_author(name="Commands for StudyBuddy")
        embed.add_field(
            name="`s.help`",
            value="Prints this message.",
            inline=False
        )
        embed.add_field(
            name="`s.add <name> <start-time> <end-time>`",
            value="Add an assignment event to your calendar. For more information about the parameters, type `s.add`.",
            inline=False
        )
        embed.add_field(
            name="`s.view`",
            value="View your calendar, one page at a time. Each page holds 10 events.",
            inline=False
        )
        embed.add_field(
            name="`s.edit <index> <start-time> <end-time>`",
            value="Edit an assignment's start and end time by its assignment index (which can be found in `s.view`). For more information, type `s.view`.",
            inline=False
        )
        embed.add_field(
            name="`s.complete <index>`",
            value="'Completes' the assignment given by its assignment index. Completing an assignment removes it from the database.",
            inline=False
        )
        embed.add_field(
            name="`s.timezone <timezone>`",
            value="Input your timezone to be used for the calendar. **NONE OF THE COMMANDS WORK WITHOUT IT!!** Timezone must be a tz-format timezone, a reference for which is available on Wikipedia.",
            inline=False
        )
        embed.add_field(
            name="`s.file`",
            value="The bot opens a DM with you where you can submit your Google Calendar file, to be imported to your local Discord calendar.",
            inline=False
        )
        embed.add_field(
            name="`s.startSession`",
            value="Start a session. You will be given a role, which identifies your pomodoro session.",
            inline=False
        )
        embed.add_field(
            name="`s.joinSession <role>`",
            value="Join a pre-existing study session specified by <role>.",
            inline=False
        )
        embed.add_field(
            name="`s.endSession <role>`",
            value="End the session specified by <role>.",
            inline=False
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TextInputter(bot))