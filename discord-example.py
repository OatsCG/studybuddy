import discord
from discord.ext import commands
# bot token: MTEwMTY3NDk5OTkxNzU4NDQxNw.GeY4j1.a9CQ-wStE51cL0-RXgQSCJyL35itEsuyFKmBKs

class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="s.",
            status=discord.Status.online,
            activity=discord.Game(name="Hacking the Pentagon"),
            intents=discord.Intents.all(),
            case_insensitive=True
        )

        self.initial_extensions = [
            'text-interface.text-input-cog',
            # 'ext.advanced_commands',
            # 'ext.events'
            # 'ext.background_tasks',
            # 'ext.handling_errors',
            # 'ext.webhooks',
            # 'ext.async_request',
            # 'ext.thread_case'
        ]

        for ext in self.initial_extensions:
            self.load_extension(ext)


bot = MyBot()
bot.run("MTEwMTY3NDk5OTkxNzU4NDQxNw.GeY4j1.a9CQ-wStE51cL0-RXgQSCJyL35itEsuyFKmBKs")

