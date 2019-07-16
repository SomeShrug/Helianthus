import os

from discord.ext import commands

PREFIX = '\\'
TOKEN = os.environ['BOT_TOKEN']

bot = commands.Bot(command_prefix=PREFIX, help_command=None)
bot.load_extension('cmd')
bot.load_extension('data')
bot.load_extension('event')


def main():
    bot.run(TOKEN)
