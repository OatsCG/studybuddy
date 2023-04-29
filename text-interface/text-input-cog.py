import discord
from discord.ext import commands
from database.database_curator import tasksDatabase

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


def setup(bot):
    bot.add_cog(Basics(bot))