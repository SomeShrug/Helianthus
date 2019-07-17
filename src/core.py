import time
from datetime import datetime
from gettext import gettext

from discord import Embed, Game
from discord.ext.commands import BadArgument, Bot, Cog, CommandError, CommandNotFound, Context, MissingPermissions, \
    MissingRequiredArgument

_ = gettext


class Core(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self._time = datetime.utcfromtimestamp(time.time())

    @Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name}')
        print(f'BOT ID : {self.bot.user.id}')
        print(f'Total Server(s) : {len(self.bot.guilds)}')
        print(f'Total Channel(s) : {len(tuple(self.bot.get_all_channels()))}')
        await self.bot.change_presence(
            activity=Game(name=f'{self.bot.command_prefix}help for commands. Why won\'t you change?'))

    @Cog.listener()
    async def on_command_error(self, ctx: Context, exception: CommandError):
        embed = Embed()
        if type(exception) is MissingPermissions:
            msg = _('You do not have the required permissions to run this command.')
        elif type(exception) is CommandNotFound:
            msg = _('Please enter a registered command.')
        elif type(exception) is MissingRequiredArgument:
            exception: MissingRequiredArgument
            msg = _(f'You are missing a required argument: `{exception.param.name}`')
        elif type(exception) is BadArgument:
            msg = _(f'Please enter a valid argument.')
        else:
            msg = f'`{type(exception).__name__}: {exception}`'
        await ctx.send(msg.format(prefix=self.bot.command_prefix))

    @Cog.listener()
    async def on_command(self, ctx: Context):
        pass


def setup(bot: Bot) -> None:
    cogs = (Core,)
    for cog in cogs:
        cog_name = cog.__name__
        if cog_name in cogs:
            bot.remove_cog(cog_name)
        bot.add_cog(cog(bot))
        print(f'Loaded cog[{cog_name}]')
    print(f'Loaded {__file__}')


SUCCESS_COLOR = 0x00c853
FAIL_COLOR = 0xd50000
