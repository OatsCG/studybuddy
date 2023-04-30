import discord
from discord.ext import commands
import os
from dotenv import load_dotenv  # pip install python-dotenv

TOKEN = os.getenv("TOKEN")

class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="s.",
            status=discord.Status.online,
            activity=discord.Game(name="type s.help to get started!"),
            intents=discord.Intents.all(),
            case_insensitive=True
        )

        self.initial_extensions = [
            'text-interface.text-input-cog',
            # 'ext.pomodoro',
        ]

        for ext in self.initial_extensions:
            self.load_extesion(ext)


bot = MyBot()
bot.run(TOKEN)