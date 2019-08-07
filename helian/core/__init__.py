import importlib

from discord.ext import commands

from . import data, embed, resource, utility

# Modules in load order
MODULES = (
    data,
    utility,
    embed,
    resource
)


def setup(bot: commands.Bot):
    del bot
    for module in MODULES:
        importlib.reload(module)
