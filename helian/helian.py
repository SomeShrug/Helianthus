import os

from discord.ext import commands

PREFIX = '\\'
TOKEN = os.environ['BOT_TOKEN']

bot = commands.Bot(command_prefix=PREFIX, help_command=None)


def main():
    bot.load_extension('core')
    bot.load_extension('cogs')
    bot.run(TOKEN)
