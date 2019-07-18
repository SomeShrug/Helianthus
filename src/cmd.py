import asyncio
import gc
import sys
import time
from copy import deepcopy
from operator import attrgetter
from random import choice
from typing import Collection, List, Optional, Union

from discord import AppInfo, Embed, FFmpegPCMAudio, Member, Reaction, TextChannel, User, VoiceChannel, VoiceClient
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Command, Context, ExtensionFailed
from math import ceil

from core import FAIL_COLOR, SUCCESS_COLOR
from data import _format_time, DBMAN, Equipment, LANGMAN, Language, TDoll
from resources import *
from resources import EMOJI_DOWN, EMOJI_LEFT, EMOJI_RIGHT, EMOJI_UP

_ = lambda x: x


def generate_help(prefix: str, command_pool: Collection[Command], chunk_size: int = 10):
    sorted_commands = sorted(command_pool, key=attrgetter('name'))
    filtered_cmds = tuple(filter(lambda x: 'is_owner' not in ''.join(tuple(map(repr, x.checks))), sorted_commands))
    cmd_gen = [filtered_cmds[n:n + chunk_size] for n in range(0, len(filtered_cmds), chunk_size)]
    embeds = []
    max_pages = len(cmd_gen)
    for page, pool in enumerate(cmd_gen, start=1):
        embed = Embed(color=SUCCESS_COLOR,
                      title=_(HELIAN_NAME))
        for command in pool:
            if command.aliases:
                name = f'`{prefix}[{"|".join((command.name, *command.aliases))}]`'
            else:
                name = f'`{prefix}{command.name}`'
            embed.add_field(name=name,
                            value=_(command.help),
                            inline=False)
            embed.set_footer(text=_(PAGINATOR_PAGE_COUNTER_STR).format(current=page, max=max_pages))
        embeds.append(embed)
    return embeds


async def _paginate(bot, ctx: Context, target: Member,
                    messages: Union[List[Embed], List[List[Embed]]]):
    current_page = 0
    current_subpage = 0

    try:
        msg = await ctx.send(embed=messages[current_page][0])
    except TypeError:
        msg = await ctx.send(embed=messages[current_page])

    if len(messages) > 1:
        await msg.add_reaction(EMOJI_LEFT)
        await msg.add_reaction(EMOJI_RIGHT)

    if len(messages[0]) > 1 and isinstance(messages[current_page], Collection):
        await msg.add_reaction(EMOJI_UP)
        await msg.add_reaction(EMOJI_DOWN)

    while True:
        try:
            has_subpage = isinstance(messages[current_page], Collection) and len(messages[current_page]) > 1

            if has_subpage:
                await msg.add_reaction(EMOJI_UP)
                await msg.add_reaction(EMOJI_DOWN)
            else:
                await msg.remove_reaction(EMOJI_UP, bot.user)
                await msg.remove_reaction(EMOJI_DOWN, bot.user)

            def check(r: Reaction, u: Member) -> bool:
                if has_subpage:
                    reaction_whitelist = (EMOJI_RIGHT, EMOJI_LEFT, EMOJI_UP, EMOJI_DOWN)
                else:
                    reaction_whitelist = (EMOJI_RIGHT, EMOJI_LEFT)
                return r.message.id == msg.id and u == target and r.emoji in reaction_whitelist

            reaction, user = await bot.wait_for('reaction_add',
                                                timeout=30,
                                                check=check)
            if reaction.emoji in (EMOJI_RIGHT, EMOJI_LEFT):
                current_page += (reaction.emoji == EMOJI_RIGHT) * 2 - 1
                current_subpage = 0
            else:
                current_subpage += (reaction.emoji == EMOJI_UP) * 2 - 1
            current_page %= len(messages)
            current_subpage %= 2
            await msg.remove_reaction(reaction.emoji, user)
            try:
                await msg.edit(embed=messages[current_page][current_subpage])
            except TypeError:
                await msg.edit(embed=messages[current_page])

        except asyncio.TimeoutError:
            await msg.clear_reactions()
            break


class Administration(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=('dcl',), help=CMD_DELCHLANG_HELP_STR)
    async def delchlang(self, ctx: Context):
        try:
            await LANGMAN.del_chlang(ctx)
        except KeyError:
            await ctx.send(_(CMD_DELCHLANG_LANG_UNASSIGNED_STR))
        else:
            await ctx.send(_(CMD_DELCHLANG_SUCCESS_STR))

    @commands.command(aliases=['h'], help=_(CMD_HELP_HELP_STR))
    async def help(self, ctx: Context, command_query: Optional[str] = None):
        if command_query is None:
            help_pages = generate_help(self.bot.command_prefix, tuple(self.bot.commands))
            await _paginate(self.bot, ctx, ctx.author, help_pages)
        else:
            command: Optional[Command] = self.bot.get_command(command_query)
            if command is not None:
                if len(command.aliases) > 1:
                    aliases = '|'.join(command.aliases)
                    usage = f'[{command.name}{aliases}]'
                else:
                    usage = command.name
                command_usage = f'{self.bot.command_prefix}{usage} {command.signature}'
                argument_desc = '\n'.join(map(str, command.clean_params.values()))
                await ctx.send(_(CMD_HELP_COMMAND_STR).format(usage=command_usage,
                                                              help=_(command.help),
                                                              params=argument_desc))
            else:
                await ctx.send(_(CMD_HELP_COMMAND_NOT_FOUND_STR))

    @commands.is_owner()
    @commands.command(aliases=['r'], help=_(CMD_RELOAD_HELP_STR))
    async def reload(self, ctx: Context):
        start_time = time.time()
        message = await ctx.send(_(CMD_RELOAD_BEGIN_STR))
        await LANGMAN.dump()
        for extension in self.bot.extensions.keys():
            try:
                self.bot.reload_extension(extension)
            except ExtensionFailed:
                continue
        await LANGMAN.reload()
        await LANGMAN.reload_lang()
        await LANGMAN.install_lang(ctx)
        seconds_elaped = time.time() - start_time
        await message.edit(content=_(CMD_RELOAD_COMPLETE_STR).format(time=seconds_elaped))

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=('sl',), help=_(CMD_SETLANG_HELP_STR))
    async def setlang(self, ctx: Context, lang: str):
        if not Language.is_lang(lang):
            locales = ", ".join(map(lambda x: f"`{x.name}`", Language.__members__.values()))
            await ctx.send(_(CMD_SETLANG_UNKNOWN_LANGUAGE_STR).format(locales=locales))
        else:
            await LANGMAN.set_slang(ctx, lang)
            await ctx.send(_(CMD_SETLANG_SUCCESS_STR).format(language=lang))

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=('scl',), help=_(CMD_SETCHLANG_HELP_STR))
    async def setchlang(self, ctx: Context, lang: str):
        if not Language.is_lang(lang):
            locales = ", ".join(map(lambda x: f"`{x.name}`", Language.__members__.values()))
            await ctx.send(_(CMD_SETCHLANG_UNKNOWN_LANGUAGE_STR).format(locales=locales))
        else:
            await LANGMAN.set_chlang(ctx, lang)
            await ctx.send(_(CMD_SETCHLANG_SUCCESS_STR).format(language=lang))

    @commands.command(help=_(CMD_STATS_HELP_STR))
    async def stats(self, ctx: Context):
        lang = await LANGMAN.get_lang(ctx)
        memory_usage = sum(map(sys.getsizeof, gc.get_objects())) / 1000000
        n_servers = len(self.bot.guilds)
        channels = self.bot.get_all_channels()
        channel_count = tuple(map(sum, zip(*((type(chan) is VoiceChannel, type(chan) is TextChannel)
                                             for chan in channels))))
        n_text, n_voice = channel_count
        invite = STATS_INVITE_URL_STR.format(id=self.bot.user.id)

        embed = Embed(color=SUCCESS_COLOR, title=HELIAN_PRODUCT_NAME.format(name=_(HELIAN_NAME),
                                                                            version=HELIAN_VERSION_STR))
        app_info: AppInfo = await self.bot.application_info()
        owner: User = app_info.owner
        embed.add_field(name=_(STATS_DEVELOPER_LBL), value=f'{owner.display_name}#{owner.discriminator}')
        embed.add_field(name=_(STATS_DEVELOPER_ID_LBL), value=owner.id)
        embed.add_field(name=_(STATS_BOT_ID_LBL), value=self.bot.user.id)
        embed.add_field(name=_(STATS_MEMORY_USAGE_LBL), value=_(STATS_MEMORY_USAGE_STR.format(memory=memory_usage)))
        embed.add_field(name=_(STATS_PRESENCE_LBL), value=_(STATS_PRESENCE_STR).format(n_servers=n_servers,
                                                                                       n_text=n_text,
                                                                                       n_voice=n_voice))
        embed.add_field(name=_(STATS_LANGUAGE_LBL), value=lang.name)
        embed.add_field(name=_(STATS_INVITE_LBL), value=invite)
        await ctx.send(embed=embed)


# TODO: Remove the need for eval
class Analytics(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    async def _gen_doll_time_msgs(lang: Language, *dolls: TDoll) -> List[Embed]:
        messages = []
        add_footer = len(dolls) > 1
        if lang not in (Language.EN, Language.KO):
            lang = Language.EN
        for page, doll in enumerate(dolls, start=1):
            msg = Embed(color=SUCCESS_COLOR)
            try:
                msg.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[::-1][lang.value])
            except IndexError:
                msg.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[Language.EN.value])
            msg.add_field(name=_(INFO_TYPE_LBL), value=doll.type)
            msg.add_field(name=_(INFO_PRODUCTION_TIME_LBL), value=doll.build_time)
            msg.add_field(name=_(INFO_RARITY_LBL), value=EMOJI_STAR * doll.rarity)
            msg.set_image(url=doll.image)
            if add_footer:
                msg.set_footer(text=_(PAGINATOR_PAGE_COUNTER_STR).format(current=page, max=len(dolls)))
            messages.append(msg)
        return messages

    # TODO: Make this not a mess
    @staticmethod
    async def _gen_doll_info_msgs(lang: Language, *dolls: TDoll) -> List[List[Embed]]:
        embeds = []
        add_footer = len(dolls) > 1
        for page, doll in enumerate(dolls, start=1):
            sub_pages = []
            embed = Embed(color=SUCCESS_COLOR)
            try:
                embed.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[::-1][lang.value])
            except IndexError:
                embed.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[Language.EN.value])
            embed.add_field(name=_(INFO_TYPE_LBL), value=doll.type)
            embed.add_field(name=_(INFO_PRODUCTION_TIME_LBL), value=doll.build_time)
            embed.add_field(name=_(INFO_RARITY_LBL), value=EMOJI_STAR * doll.rarity)
            embed.add_field(name=_(INFO_ID_LBL), value=str(doll.id), inline=False)
            embed.add_field(name=_(INFO_BUFF_LBL),
                            value=_(INFO_BUFF_STR).format(tiles=doll.buff,
                                                          description=eval(doll.buff_desc)[lang.value]),
                            inline=False)
            embed.add_field(name=_(INFO_SKILL_LBL),
                            value=INFO_SKILL_STR.format(name=eval(doll.slname)[lang.value],
                                                        description=eval(doll.sldesc)[lang.value]))
            embed.add_field(name=_(INFO_ARTIST_LBL), value=doll.artist)
            embed.add_field(name=_(INFO_CV_LBL), value=doll.cv)
            embed.set_image(url=doll.image)
            mod = None
            if doll.mod_rarity:
                mod = deepcopy(embed)
                sl_trans = tuple(map(lambda x: eval(x)[lang.value],
                                     (doll.mod_s1_name, doll.mod_s1_desc, doll.mod_s2_name, doll.mod_s2_desc)))
                skill_str = '\n'.join([INFO_SKILL_STR.format(name=sl_trans[i],
                                                             description=sl_trans[i + 1]) for i in range(0, 4, 2)])
                mod.set_field_at(3, name=_(INFO_RARITY_LBL), value=EMOJI_STAR * doll.mod_rarity)
                tile_str = doll.mod_tile if doll.mod_tile else doll.buff
                mod.set_field_at(5, name=_(INFO_BUFF_LBL),
                                 value=INFO_BUFF_STR.format(tiles=tile_str,
                                                            description=eval(doll.mod_buff)[lang.value]))
                mod.set_field_at(6, name=_(INFO_SKILLS_LBL), value=skill_str)
                mod.set_image(url=doll.mod_image)

            if add_footer:
                page_ctr = _(PAGINATOR_PAGE_COUNTER_STR).format(current=page, max=len(dolls))
                if doll.mod_rarity and mod is not None:
                    footer = PAGINATOR_FOOTER_STR.format(page=page_ctr,
                                                         sub_page=_(PAGINATOR_SUBPAGE_COUNTER_STR).format(current=1,
                                                                                                          max=2))
                    mod_footer = PAGINATOR_FOOTER_STR.format(page=page_ctr,
                                                             sub_page=_(PAGINATOR_SUBPAGE_COUNTER_STR).format(current=2,
                                                                                                              max=2))
                    mod.set_footer(text=mod_footer)
                else:
                    footer = PAGINATOR_FOOTER_STR.format(page=page_ctr, sub_page='')
                embed.set_footer(text=footer)

            sub_pages.append(embed)
            if mod is not None:
                sub_pages.append(mod)

            embeds.append(sub_pages)

        return embeds

    @staticmethod
    async def _gen_equip_time_msgs(lang: Language, *equips: Equipment) -> List[Embed]:
        embeds = []
        add_footer = len(equips) > 1
        for page, equip in enumerate(equips, start=1):
            embed = Embed(color=SUCCESS_COLOR)

            embed.add_field(name=_(INFO_NAME_LBL), value=eval(equip.name)[lang.value])
            embed.add_field(name=_(INFO_TYPE_LBL), value=eval(equip.type)[lang.value])
            embed.add_field(name=_(INFO_PRODUCTION_TIME_LBL), value=equip.time)
            if equip.rarity is None:
                embed.add_field(name=_(INFO_STATS_LBL),
                                value=eval(equip.stats)[lang.value],
                                inline=False)
                embed.add_field(name=_(INFO_SKILL_LBL),
                                value=INFO_SKILL_STR.format(name=eval(equip.slname)[lang.value],
                                                            description=eval(equip.sldesc)[lang.value]))
                embed.set_image(url=equip.image)
            else:
                embed.add_field(name=_(INFO_RARITY_LBL), value=EMOJI_STAR * equip.rarity)
                embed.set_thumbnail(url=equip.image)
            if add_footer:
                embed.set_footer(text=_(PAGINATOR_PAGE_COUNTER_STR).format(current=page,
                                                                           max=len(equips)))

            embeds.append(embed)
        return embeds

    @commands.command(aliases=['d'], help=_(CMD_DOLL_HELP_STR))
    async def doll(self, ctx: Context, prod_time: str):
        prod_time = await _format_time(prod_time)
        if prod_time is None:
            await ctx.send(_(TIME_FORMAT_ERROR_STR))
            return
        dolls = DBMAN.tdoll_from_time(prod_time)
        messages = await self._gen_doll_time_msgs(await LANGMAN.get_lang(ctx), *dolls)

        if len(dolls) > 1:
            await _paginate(self.bot, ctx, ctx.author, messages)
        elif dolls:
            await ctx.send(embed=messages[-1])
        else:
            await ctx.send(_(CMD_DOLL_DOLL_NOT_FOUND_STR))

    @commands.command(aliases=['e'], help=_(CMD_EQUIP_HELP_STR))
    async def equip(self, ctx: Context, production_time: str):
        production_time = await _format_time(production_time)
        if production_time is None:
            await ctx.send(_(TIME_FORMAT_ERROR_STR))
            return
        equipment = DBMAN.equip_from_time(production_time)
        messages = await self._gen_equip_time_msgs(await LANGMAN.get_lang(ctx), *equipment)
        if len(equipment) > 1:
            await _paginate(self.bot, ctx, ctx.author, messages)
        elif equipment:
            await ctx.send(embed=messages[-1])
        else:
            await ctx.send(_(CMD_EQUIP_EQUIP_NOT_FOUND_STR))

    @commands.command(help=_(CMD_EXP_HELP_STR))
    async def exp(self,
                  ctx: Context,
                  start_level: int,
                  exp: int,
                  target_level: int,
                  oath: Optional[bool] = False):

        color = FAIL_COLOR
        if not 1 <= start_level <= DBMAN.max_level:
            msg = _(CMD_EXP_INVALID_START_LEVEL_STR)
        elif not 1 <= target_level <= DBMAN.max_level:
            msg = _(CMD_EXP_INVALID_TARGET_LEVEL_STR)
        elif target_level <= start_level:
            msg = _(CMD_EXP_TARGET_LESS_THAN_START_STR).format(level=start_level)
        else:
            start_exp = DBMAN.exp_from_level(start_level)
            start_exp += exp
            try:
                actual_start, left_over = DBMAN.level_from_exp(start_exp)

            except ValueError:
                msg = _(CMD_EXP_INVALID_EXP_STR)
            else:
                if actual_start >= target_level:
                    msg = _(CMD_EXP_REPORT_UNNCESSARY_STR)
                else:
                    color = SUCCESS_COLOR
                    actual_exp = DBMAN.exp_from_level(actual_start) + left_over
                    if target_level > 100:
                        target_exp = DBMAN.exp_from_level(100)
                        mod_exp = DBMAN.exp_from_level(target_level) - target_exp
                    else:
                        target_exp = DBMAN.exp_from_level(target_level)
                        mod_exp = 0
                    target_exp += mod_exp // (oath + 1)

                    exp_diff = (target_exp - actual_exp)
                    reports = ceil(exp_diff / 3000)
                    msg = _(CMD_EXP_OUTPUT_STR).format(start=actual_start,
                                                       exp=left_over,
                                                       target=target_level,
                                                       reports=reports,
                                                       exp_difference=exp_diff)
        embed = Embed(color=color, description=msg)
        await ctx.send(embed=embed)

    @commands.command(help=_(CMD_DINFO_HELP_STR))
    async def dinfo(self, ctx: Context, alias: str):
        dolls = DBMAN.tdoll_from_name(DB_TDOLL_ALIAS_STR.format(alias=alias))
        if dolls is None or not dolls:
            await ctx.send(_(CMD_DINFO_DOLL_NOT_FOUND_STR))
        else:
            messages = await self._gen_doll_info_msgs(await LANGMAN.get_lang(ctx), *dolls)
            await _paginate(self.bot, ctx, ctx.author, messages)

    @commands.command(aliases=['rand'], help=_(CMD_RANDOM_HELP_STR))
    async def random(self, ctx: Context):
        doll = DBMAN.random_doll()
        messages = await self._gen_doll_info_msgs(await LANGMAN.get_lang(ctx), doll)
        await _paginate(self.bot, ctx, ctx.author, messages)


class Fun(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=['av'], help=_(CMD_AVATAR_HELP_STR))
    async def avatar(self, ctx: Context, user: Optional[Member] = None):
        msg = Embed(color=SUCCESS_COLOR)
        if user is None:
            msg.title = f'{ctx.author.name}#{ctx.author.discriminator}'
            msg.set_image(url=ctx.author.avatar_url)
        elif isinstance(user, Member):
            msg.title = f'{user.name}#{user.discriminator}'
            msg.set_image(url=user.avatar_url)
        await ctx.send(embed=msg)

    @commands.command(aliases=['ch'], help=_(CMD_CHOOSE_HELP_STR))
    async def choose(self, ctx: Context, *content: str):
        if not all(content):
            await ctx.send(_(CMD_CHOOSE_EMPTY_INPUT_STR))
        else:
            await ctx.send(choice(content))

    @commands.is_owner()
    @commands.command(help=_(CMD_IDW_HELP_STR))
    async def idw(self, ctx: Context, user: Optional[Member] = None):
        if user is None:
            v = ctx.author.voice
        else:
            v = user.voice

        if v is None:
            await ctx.send(_(CMD_IDW_MENTION_NOT_IN_VOICE_STR))
        else:
            c: VoiceChannel = v.channel
            vc: VoiceClient = await c.connect()
            vc.play(FFmpegPCMAudio('assets/sound/IDW_GAIN_JP.ogg'))
            while vc.is_playing():
                await asyncio.sleep(1)
            vc.stop()
            await vc.disconnect()

    @commands.is_owner()
    @commands.command(aliases=['s'], help=_(CMD_SAY_HELP_STR))
    async def say(self, ctx: Context, *, content: str):
        await ctx.message.delete()
        await ctx.send(content)


def setup(bot: Bot):
    cogs = (Administration, Analytics, Fun)
    for cog in cogs:
        cog_name = cog.__name__
        if cog_name in bot.cogs:
            bot.remove_cog(cog_name)
        bot.add_cog(cog(bot))
        print(f'Loaded cog[{cog_name}]')
    print(f'Loaded {__file__}')
