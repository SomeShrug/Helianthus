import traceback

from discord.ext import commands

from .administration import Administration
from .analytics import Analytics
from .core import Core
from .fun import Fun

# Cogs arranged in load order
COGS = (
    Core,
    Administration,
    Analytics,
    Fun
)


def setup(bot: commands.Bot):
    if not bot.cogs:
        for cog in COGS:
            bot.add_cog(cog(bot))
    else:
        for cog_name in bot.cogs.keys():
            # noinspection PyBroadException
            try:
                bot.remove_cog(cog_name)
                bot.add_cog(cog_name)
            except Exception:
                print(traceback.format_exc())
