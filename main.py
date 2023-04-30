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
        for ext in self.initial_extensions:
            self.load_extension(ext)

bot = mainBot()
bot.run("MTEwMTY3MTM3MjE3MTc4ODM5OQ.GTcS3t.8MbLzaZt4AS4Lmzz47ltq9NvfRz4aaw2tKISbE")