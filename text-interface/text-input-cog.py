import discord
from discord.ext import commands
from database.database_curator import tasksDatabase
from datetime import datetime
import asyncio
import os
from database.ics_parser import parse_ics
import math
from datetime import datetime
import pytz

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
            embed.set_footer(text="s.add")
            await ctx.reply(embed=embed)
            return
        if self._database.get_user(ctx.author.id) is None:
            embed = discord.Embed(color=discord.Colour.blurple())
            embed.add_field(name="You have not registered a timezone, use **s.timezone**", value="")
            await ctx.reply(embed=embed)
            return
        new_task_assert = self._database.add_new_task(ctx.author.id, task_title, task_startdate, task_enddate)
        if not new_task_assert:
            embed = discord.Embed(color=discord.Colour.blurple())
            embed.add_field(name=f"Error creating new user with id {ctx.author.id}", value="")
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
        # just gonna print out the first 10 tasks 
        # Reminder: format is "name", "startdate", "enddate"
        events = self._database.get_user_tasks(ctx.author.id)
        page_size = 10  # define the page size
        num_pages = math.ceil(len(events) / page_size)  # useful for determining bounds of page_number
        page_number = 3  # counting starts at 1, not 0.

        print(events[(page_number-1)*page_size:min(page_number*page_size, len(events))])  # prints out page_size items per page

        # figuring out time stuff

        # first i need to get the user's timezone
        user_info = self._database.get_user(ctx.author.id)
        time_zone = user_info['timezone']
        time_zone = pytz.timezone(time_zone)

        # Step 3: Making it look pretty!!
        embed = discord.Embed()
        embed.set_author(name=f"{ctx.author.name}'s Calendar", icon_url=ctx.author.avatar.url)  # author
        embed.set_footer(text=f"Displaying {(page_number - 1) * 10 + 1} to {(page_number) * 10} of {len(events)}")
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
                value=field_value
            )

        # now i need to add the buttons
        class MyView(discord.ui.View):

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.danger)
            async def on_prev(self, button, interaction):

                embed = interaction.message.embeds[0]
                old_page_number = max(math.ceil(int(embed.footer.text.split(' ')[1]) / 10) - 1, 1)

                page_of_events = events[(old_page_number - 1) * page_size:min(old_page_number * page_size, len(events))]
                new_embed = discord.Embed()
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
                        value=field_value
                    )
                await interaction.response.edit_message(view=self, embed=new_embed)

            @discord.ui.button(label="Next", style=discord.ButtonStyle.success)
            async def on_next(self, button, interaction):
                embed = interaction.message.embeds[0]

                old_page_number = min(math.ceil(int(embed.footer.text.split(' ')[1]) / 10) + 1, num_pages)

                page_of_events = events[(old_page_number - 1) * page_size:min(old_page_number * page_size, len(events))]
                new_embed = discord.Embed()
                new_embed.set_author(name=embed.author.name, icon_url=embed.author.url)
                new_embed.set_footer(text=f"Displaying {(old_page_number - 1) * 10 + 1} to {(old_page_number) * 10} of {len(events)}")
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
                        value=field_value
                    )

                embed = new_embed
                await interaction.response.edit_message(view=self, embed=embed)

        await ctx.send(embed=embed, view=MyView())


    
    @commands.command(name="complete", aliases=["remove", "delete"])
    async def complete(self, ctx, channel: discord.TextChannel, text: str):
        #remove task from database
        await channel.send(text)

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