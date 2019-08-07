import datetime
import operator
import time
import traceback
from typing import Optional

import discord
from discord.ext import commands

from core.data import SETMAN
from core.embed import paginate
from core.resource import *

_ = lambda x: x
del _


def gen_cmd_usage(prefix: str, command: commands.Command) -> str:
    if command.aliases:
        call_usage = f'[{"|".join((command.name, *command.aliases))}]'
    else:
        call_usage = command.name
    return f'{prefix}{call_usage} {command.signature}'


def gen_help(prefix: str, *command_pool: commands.Command, chunk_size: int = 5):
    embeds = []
    sorted_commands = sorted(command_pool, key=operator.attrgetter('name'))
    filtered_cmds = tuple(filter(lambda x: 'is_owner' not in ''.join(tuple(map(repr, x.checks))), sorted_commands))
    cmd_gen = [filtered_cmds[n:n + chunk_size] for n in range(0, len(filtered_cmds), chunk_size)]
    max_pages = len(cmd_gen)
    for page, pool in enumerate(cmd_gen, start=1):
        embed = discord.Embed(color=SUCCESS_COLOR,
                              title=_(HELIAN_NAME))
        for command in pool:
            embed.add_field(name=f'```{gen_cmd_usage(prefix, command)}```',
                            value=_(command.help),
                            inline=False)
        embed.set_footer(text=_(INFO_PAGE_COUNTER_STR).format(current=page, max=max_pages))
        embeds.append(embed)
    return embeds


class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._time = datetime.datetime.utcfromtimestamp(time.time())

    @commands.group(aliases=['h'], help=_(CMD_HELP_HELP_STR))
    async def help(self, ctx: commands.Context, query: Optional[str] = None):
        if query is not None:
            command: Optional[commands.Command] = self.bot.get_command(query)
            if command is not None:
                argument_desc = '\n'.join(map(str, command.clean_params.values()))
                await ctx.send(_(CMD_HELP_COMMAND_STR).format(usage=gen_cmd_usage(self.bot.command_prefix, command),
                                                              help=_(command.help),
                                                              params=argument_desc))
            else:
                await ctx.send(_(CMD_HELP_COMMAND_NOT_FOUND_STR))
        else:
            help_pages = gen_help(self.bot.command_prefix, *self.bot.commands)
            await paginate(self.bot, ctx, ctx.author, help_pages)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name}')
        print(f'BOT ID : {self.bot.user.id}')
        print(f'Total Server(s) : {len(self.bot.guilds)}')
        print(f'Total Channel(s) : {len(tuple(self.bot.get_all_channels()))}')
        await self.bot.change_presence(
            activity=discord.Game(name=HELIAN_PRESENCE.format(prefix=self.bot.command_prefix)))
        self.bot.owner_id = (await self.bot.application_info()).owner.id

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exception: discord.DiscordException):
        if type(exception) is commands.MissingPermissions:
            msg = _('You do not have the required permissions to run this command.')
        elif type(exception) is commands.CommandNotFound:
            msg = _('Please enter a registered command.')
        elif type(exception) is commands.MissingRequiredArgument:
            exception: commands.MissingRequiredArgument
            msg = _(f'You are missing a required argument: `{exception.param.name}`')
        elif type(exception) is commands.BadArgument:
            msg = _(f'Please enter a valid argument.')
        elif type(exception) is commands.CommandInvokeError:
            exception: commands.CommandInvokeError
            msg = _(CMD_DEPRECATED_WARNING_STR).format(prefix=self.bot.command_prefix,
                                                       alternate=exception.original.args[0])
        else:
            trace = '\n'.join(
                traceback.format_exception(type(exception), exception, exception.__traceback__))
            msg = f'```{trace}```'
        await ctx.send(msg.format(prefix=self.bot.command_prefix))

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        await self.bot.wait_until_ready()
        await SETMAN.install_lang(ctx)

    @commands.is_owner()
    @commands.command(aliases=['r'], help=_(CMD_RELOAD_HELP_STR))
    async def reload(self, ctx: commands.Context):
        start_time = time.time()
        message = await ctx.send(_(CMD_RELOAD_BEGIN_STR))
        await SETMAN.dump()
        for extension in self.bot.extensions.keys():
            self.bot.reload_extension(extension)
        await SETMAN.install_lang(ctx)
        seconds_elaped = time.time() - start_time
        await message.edit(content=_(CMD_RELOAD_COMPLETE_STR).format(time=seconds_elaped))
