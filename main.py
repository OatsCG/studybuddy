import discord
from discord.ext import commands
class mainBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="s.",
            status=discord.Status.online,
            activity=discord.Game(name="i love sta256"),
            intents=discord.Intents.all(),
            case_insensitive=True
        )
        self.initial_extensions = ['ext.pomodoro']

    async def setup_ext(self):
        for ext in self.initial_extensions:
            await self.load_extension(ext)
bot = mainBot()
bot.setup_ext
bot.run("MTEwMTY3MTM3MjE3MTc4ODM5OQ.G_C3Co.ju76tu0q8bsiUgf2QDzachdbONSg41cHgFJg4g")