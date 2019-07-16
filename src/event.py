from discord import Game
from discord.ext.commands import Bot, Cog, CommandNotFound, Context, MissingPermissions

from data import LANGMAN


class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name}')
        print(f'BOT ID : {self.bot.user.id}')
        print(f'Total Server(s) : {len(self.bot.guilds)}')
        print(f'Total Channel(s) : {len(tuple(self.bot.get_all_channels()))}')
        await self.bot.change_presence(
            activity=Game(name=f'{self.bot.command_prefix}help for commands'))

    @Cog.listener()
    async def on_command_error(self, ctx: Context, exception: CommandError):
        if type(exception) is MissingPermissions:
            msg = await LANGMAN.get_string(ctx, 'error', 'missing_perms')
        elif type(exception) is CommandNotFound:
            msg = await LANGMAN.get_string(ctx, 'error', 'cmd_not_found')
        else:
            return
        await ctx.send(msg.format(prefix=self.bot.command_prefix))

    @Cog.listener()
    async def on_command(self, ctx: Context):
        pass


def setup(bot: Bot) -> None:
    cog_name = Events.__class__.__name__
    if cog_name in bot.cogs:
        bot.remove_cog(cog_name)
    bot.add_cog(Events(bot))
    print(f'Loaded {__file__}')
