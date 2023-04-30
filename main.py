import discord
from discord.ext import commands
import os
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

class mainBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="s.",
            status=discord.Status.online,
            activity=discord.Game(name="type s.help to get started!"),
            intents=discord.Intents.all(),
            case_insensitive=True
        )

        self.remove_command("help")

        self.initial_extensions = [
            'text-interface.text-input-cog',
            # 'ext.pomodoro',
        ]

        for ext in self.initial_extensions:
            self.load_extension(ext)


bot = MyBot()
bot.run(TOKEN)