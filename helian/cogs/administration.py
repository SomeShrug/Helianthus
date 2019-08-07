from discord.ext import commands

from core.data import Language, SETMAN
from core.embed import construct_statistic_embed
from core.resource import *
from core.utility import mono

_ = lambda x: x
del _


async def no_subcommand_callback():
    print('test')


class Administration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name='settings', aliases=('set',), invoke_without_command=True)
    async def setting_hub(self, ctx: commands.Context):
        await ctx.send(
            f'Please specify one of the available settings: '
            f'{", ".join(map(lambda command: mono(command.name), self.setting_hub.commands))}')

    @setting_hub.group(name='language', aliases=('lang',), invoke_without_command=True)
    async def language_setting(self, ctx: commands.Context):
        await ctx.send(
            f'Please specify one of the available actions: '
            f'{", ".join(map(lambda command: mono(command.name), self.language_setting.commands))}')

    @language_setting.group(name='set', invoke_without_command=True)
    async def language_setter(self, ctx: commands.Context):
        await ctx.send(
            f'Please specify one of the available regions: '
            f'{", ".join(map(lambda command: mono(command.name), self.language_setter.commands))}')

    @language_setter.command(name='server', aliases=('sv',))
    async def set_server_language(self, ctx: commands.Context, language: str):
        if not Language.is_lang(language):
            locales = ", ".join(map(lambda lang: mono(lang.name), Language.__members__.values()))
            await ctx.send(_(CMD_SETLANG_UNKNOWN_LANGUAGE_STR).format(locales=locales))
        else:
            await SETMAN.set_slang(ctx, language)
            await ctx.send(_(CMD_SETLANG_SUCCESS_STR).format(language=language.upper()))

    @language_setter.command(name='channel', aliases=('ch',))
    async def set_channel_language(self, ctx: commands.Context, language: str):
        if not Language.is_lang(language):
            locales = ", ".join(map(lambda lang: mono(lang.name), Language.__members__.values()))
            await ctx.send(_(CMD_SETCHLANG_UNKNOWN_LANGUAGE_STR).format(locales=locales))
        else:
            await SETMAN.set_chlang(ctx, language)
            await ctx.send(_(CMD_SETCHLANG_SUCCESS_STR).format(language=language.upper()))

    @language_setting.command(name='unset', aliases=('u',))
    async def unset_channel_language(self, ctx: commands.Context):
        try:
            await SETMAN.del_chlang(ctx)
        except KeyError:
            await ctx.send(_(CMD_DELCHLANG_LANG_UNASSIGNED_STR))
        else:
            await ctx.send(_(CMD_DELCHLANG_SUCCESS_STR))

    @commands.command(help=_(CMD_STATS_HELP_STR))
    async def stats(self, ctx: commands.Context):
        await ctx.send(embed=construct_statistic_embed(await SETMAN.get_lang(ctx), self.bot))
