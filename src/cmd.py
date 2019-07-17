import asyncio
import gc
import sys
import time
from copy import deepcopy
from gettext import gettext
from random import choice
from typing import Collection, List, Optional, Union

from discord import AppInfo, Embed, FFmpegPCMAudio, Member, Reaction, TextChannel, VoiceChannel, VoiceClient
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Command, Context
from math import ceil

from core import FAIL_COLOR, SUCCESS_COLOR
from data import _format_time, DBMAN, Equipment, LANGMAN, Language, TDoll

RIGHT = '\u27A1'
LEFT = '\u2B05'
UP = '\u2B06'
DOWN = '\u2B07'

_ = gettext

HELP_TEMPLATE = """```
USAGE
-----
{usage}

HELP
----
{help}

PARAMETERS
----------
{params}
```
"""


def generate_help(prefix: str, command_pool: Collection[Command], chunk_size: int = 10):
    filtered_cmds = tuple(filter(lambda x: 'is_owner' not in ''.join(tuple(map(repr, x.checks))), command_pool))
    cmd_gen = [filtered_cmds[n:n + chunk_size] for n in range(0, len(filtered_cmds), chunk_size)]
    embeds = []
    for page, pool in enumerate(cmd_gen, start=1):
        embed = Embed(color=SUCCESS_COLOR,
                      title=_('Helianthus v2.0'))
        for command in pool:
            if command.aliases:
                name = f'`{prefix}[{"|".join((command.name, *command.aliases))}]`'
            else:
                name = f'`{prefix}{command.name}`'
            embed.add_field(name=name,
                            value=command.help,
                            inline=False)
            embed.set_footer(text=f'Page {page}/{len(cmd_gen)}')
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
        await msg.add_reaction(LEFT)
        await msg.add_reaction(RIGHT)

    if len(messages[0]) > 1 and isinstance(messages[current_page], Collection):
        await msg.add_reaction(UP)
        await msg.add_reaction(DOWN)

    while True:
        try:
            has_subpage = isinstance(messages[current_page], Collection) and len(messages[current_page]) > 1

            if has_subpage:
                await msg.add_reaction(UP)
                await msg.add_reaction(DOWN)
            else:
                await msg.remove_reaction(UP, bot.user)
                await msg.remove_reaction(DOWN, bot.user)

            def check(r: Reaction, u: Member) -> bool:
                if has_subpage:
                    reaction_whitelist = (RIGHT, LEFT, UP, DOWN)
                else:
                    reaction_whitelist = (RIGHT, LEFT)
                return r.message.id == msg.id and u == target and r.emoji in reaction_whitelist

            reaction, user = await bot.wait_for('reaction_add',
                                                timeout=30,
                                                check=check)
            if reaction.emoji in (RIGHT, LEFT):
                current_page += (reaction.emoji == RIGHT) * 2 - 1
                current_subpage = 0
            else:
                current_subpage += (reaction.emoji == UP) * 2 - 1
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
    @commands.command(aliases=('dcl',),
                      help=_('Have Helian unset a channel\'s language.'))
    async def delchlang(self, ctx: Context):
        try:
            LANGMAN.del_chlang(ctx)
        except KeyError:
            await ctx.send(_('This channel does not have an assigned language.'))
        else:
            await ctx.send(_('This channel\'s language has been successfully deleted.'))

    @commands.command(aliases=['h'],
                      help=_('Have Helian get you some help.'))
    async def help(self, ctx: Context, command_query: Optional[str] = None):
        if command_query is None:
            help_pages = generate_help(self.bot.command_prefix, tuple(self.bot.commands))
            await _paginate(self.bot, ctx, ctx.author, help_pages)
        else:
            target_command: Optional[Command] = self.bot.get_command(command_query)
            if target_command is not None:
                if len(target_command.aliases) > 1:
                    aliases = '|'.join(target_command.aliases)
                    usage = f'[{target_command.name}{aliases}]'
                else:
                    usage = target_command.name
                command_usage = f'{self.bot.command_prefix}{usage} {target_command.signature}'
                argument_desc = '\n'.join(map(str, target_command.clean_params.values()))
                await ctx.send(HELP_TEMPLATE.format(usage=command_usage,
                                                    help=target_command.help,
                                                    params=argument_desc))
            else:
                await ctx.send(_('That command does not exist.'))

    @commands.is_owner()
    @commands.command(aliases=['r'],
                      help=_('Have Helian reload her databases.'))
    async def reload(self, ctx: Context):
        start = time.time()
        await LANGMAN.dump()
        self.bot.reload_extension('data')
        message = await ctx.send(_('Reloaded data managers.'))
        self.bot.reload_extension('core')
        await message.edit(content=_('Reloaded event manager.'))
        self.bot.reload_extension('cmd')
        await message.edit(content=_('Reloaded commands.'))
        elapsed = time.time() - start
        await message.edit(
            content=_('Reload complete. Elapsed time: {:.2f} seconds').format(
                elapsed))

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=('sl',),
                      help=_('Have Helian set the server language.'))
    async def setlang(self, ctx: Context, lang: str):
        if not Language.is_lang(lang):
            await ctx.send(_('You have entered an unsupported or unknown language. The following locales are supported:'
                             f' {", ".join(map(lambda x: f"`{x.name}`", Language.__members__.values()))}'))
        else:
            await LANGMAN.set_slang(ctx, lang)
            await ctx.send(_(f'This server\'s language has been set to: {lang}'))

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=('scl',),
                      help=_('Have Helian set a channel\'s language'))
    async def setchlang(self, ctx: Context, lang: str):
        if not Language.is_lang(lang):
            await ctx.send(_('You have entered an unsupported or unknown language. The following locales are supported:'
                             f' {", ".join(map(lambda x: f"`{x.name}`", Language.__members__.values()))}'))
        else:
            await LANGMAN.set_chlang(ctx, lang)
            await ctx.send(_(f'This channel\'s language has been set to: {lang}'))

    @commands.command(help=_('Get Helian\'s performance statistics'))
    async def stats(self, ctx: Context):
        lang = await LANGMAN.get_lang(ctx)
        memory_usage = sum(map(sys.getsizeof, gc.get_objects())) / 1000000
        n_servers = len(self.bot.guilds)
        channels = self.bot.get_all_channels()
        counts = tuple(map(sum, zip(*[(type(chan) == VoiceChannel, type(chan) == TextChannel) for chan in channels])))
        txt_chans, v_chans = counts
        invite = f'https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=66186303'

        embed = Embed(color=SUCCESS_COLOR, title=_('Helianthus v2.0'))
        app_info: AppInfo = await self.bot.application_info()
        embed.add_field(name=_('Developer'), value=app_info.owner.display_name)
        embed.add_field(name=_('Developer ID'), value=self.bot.owner_id)
        embed.add_field(name=_('Helian\'s ID'), value=self.bot.user.id)
        embed.add_field(name=_('Memory Usage'), value=f'{memory_usage:.2f} MB')
        embed.add_field(name=_('Presence'),
                        value=f'Servers: {n_servers}\nText Channels: {txt_chans}\nVoice Channels: {v_chans}')
        embed.add_field(name=_('Server Language'), value=lang.name)
        embed.add_field(name=_('Invite Link'), value=invite)
        await ctx.send(embed=embed)


# TODO: Remove the need for eval
class Analytics(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    async def _gen_doll_time_msgs(lang: Language, *dolls: TDoll) -> List[Embed]:
        messages = []
        add_footer = len(dolls) > 1
        for page, doll in enumerate(dolls, start=1):
            msg = Embed(color=SUCCESS_COLOR)
            msg.add_field(name=_('Name'), value=eval(doll.name)[lang.value])
            msg.add_field(name=_('Type'), value=doll.type)
            msg.add_field(name=_('Production Time'), value=doll.build_time)
            msg.add_field(name=_('Rarity'), value=f'{doll.rarity} {_("Stars")}')
            msg.set_image(url=doll.image)
            if add_footer:
                msg.set_footer(text=f'Page {page}/{len(dolls)}')
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
            embed.add_field(name=_('Name'), value=eval(doll.name)[0])
            embed.add_field(name=_('Type'), value=doll.type)
            embed.add_field(name=_('Production Time'), value=doll.build_time)
            embed.add_field(name=_('Rarity'), value=f'{doll.rarity} {_("Stars")}')
            embed.add_field(name=_('ID'), value=f'{doll.id}', inline=False)
            embed.add_field(name=_('Tile Coverage'), value=f'{doll.buff}\n{eval(doll.buff_desc)[lang.value]}',
                            inline=False)
            embed.add_field(name=_('Skill'),
                            value=f'**{eval(doll.slname)[lang.value]}**\n{eval(doll.sldesc)[lang.value]}')
            embed.add_field(name=_('Artist'), value=doll.artist)
            embed.add_field(name=_('CV'), value=doll.cv)
            embed.set_image(url=doll.image)
            footer_template = '{page_counter} {sub_counter}'
            page_template = 'Page {page}/{max_pages}'
            sub_template = 'Subpage {page}/2'
            mod = None
            if doll.mod_rarity:
                mod = deepcopy(embed)
                sl_trans = tuple(map(lambda x: eval(x)[lang.value],
                                     (doll.mod_s1_name, doll.mod_s1_desc, doll.mod_s2_name, doll.mod_s2_desc)))
                skill_str = '\n'.join([f'**{sl_trans[i]}**\n{sl_trans[i + 1]}' for i in range(0, 4, 2)])
                mod.set_field_at(3, name=_('Rarity'), value=f'{doll.mod_rarity} {_("Stars")}')
                tile_str = doll.mod_tile if doll.mod_tile else doll.buff
                mod.set_field_at(5, name=_('Tile Coverage'), value=f'{tile_str}\n{eval(doll.mod_buff)[lang.value]}')
                mod.set_field_at(6, name=_('Skills'), value=skill_str)
                mod.set_image(url=doll.mod_image)

            if add_footer:
                page_counter = page_template.format(page=page, max_pages=len(dolls))
                if doll.mod_rarity and mod is not None:
                    footer = footer_template.format(page_counter=page_counter,
                                                    sub_counter=sub_template.format(page=1))
                    mod_footer = footer_template.format(page_counter=page_counter,
                                                        sub_counter=sub_template.format(page=2))
                    mod.set_footer(text=mod_footer)
                else:
                    footer = footer_template.format(page_counter=page_counter,
                                                    sub_counter='')
                embed.set_footer(text=footer)

            sub_pages.append(embed)
            if mod is not None:
                sub_pages.append(mod)

            embeds.append(sub_pages)

        return embeds

    @staticmethod
    async def _gen_equip_time_msgs(*equips: Equipment) -> List[Embed]:
        embeds = []
        add_footer = len(equips) > 1
        for page, equip in enumerate(equips, start=1):
            embed = Embed(color=SUCCESS_COLOR)
            embed.add_field(name=_('Name'), value=eval(equip.name)[0])
            embed.add_field(name=_('Type'), value=eval(equip.type)[0])
            embed.add_field(name=_('Production Time'), value=equip.time)
            embed.add_field(name=_('Rarity'),
                            value=f'{equip.rarity} {_("Stars")}')
            embed.set_thumbnail(url=equip.image)
            if add_footer:
                embed.set_footer(text=f'Page {page}/{len(equips)}')
            embeds.append(embed)
        return embeds

    @commands.command(aliases=['d'],
                      help=_('Have Helian lookup T-Dolls from production times.'))
    async def doll(self, ctx: Context, prod_time: str):
        prod_time = await _format_time(prod_time)
        if prod_time is None:
            await ctx.send(_('Please enter a valid production time.'))
            return
        dolls = DBMAN.tdoll_from_time(prod_time)
        messages = await self._gen_doll_time_msgs(await LANGMAN.get_lang(ctx), *dolls)

        if len(dolls) > 1:
            await _paginate(self.bot, ctx, ctx.author, messages)
        elif dolls:
            await ctx.send(embed=messages[-1])
        else:
            await ctx.send(_('There are no T-Dolls with the selected production time.'))

    @commands.command(aliases=['e'],
                      help=_('''\
                      Have Helian lookup equipment from production times.
                      Pass in a time in the %H:%M or %H%M format, where %H is a optionally 
                      0-padded two-digit hour and %M is an optionally 0-padded two digit 
                      minute.
                      
                      Examples: 12:34, 1:2 (01:02), 12:3 (12:03), 12 (00:12), 123 (01:23)
                      '''))
    async def equip(self, ctx: Context, production_time: str):
        production_time = await _format_time(production_time)
        if production_time is None:
            await ctx.send(_('Please enter a valid production time.'))
            return
        equipment = DBMAN.equip_from_time(production_time)
        messages = await self._gen_equip_time_msgs(await LANGMAN.get_lang(ctx), *equipment)
        if len(equipment) > 1:
            await _paginate(self.bot, ctx, ctx.author, messages)
        elif equipment:
            await ctx.send(embed=messages[-1])
        else:
            await ctx.send(_('There are no pieces of equipment with the selected production time.'))

    @commands.command(help=_('Have Helian calculate the number of combat reports required for leveling T-Dolls.\n'
                             'Pass in \'yes\'/\'no\' or any amalgamation of those two for the "oath" parameter.'))
    async def exp(self,
                  ctx: Context,
                  start_level: int,
                  exp: int,
                  target_level: int,
                  oath: Optional[bool] = False):

        color = FAIL_COLOR
        if not 1 <= start_level <= DBMAN.max_level:
            msg = _('Please enter a valid starting level.')
        elif not 1 <= target_level <= DBMAN.max_level:
            msg = _('Please enter a valid target level.')
        elif target_level <= start_level:
            msg = _('Please enter a target level greater than the current level.')
        else:
            start_exp = DBMAN.exp_from_level(start_level)
            start_exp += exp
            try:
                actual_start, left_over = DBMAN.level_from_exp(start_exp)

            except ValueError:
                msg = _('Please enter a valid amount of EXP.')
            else:
                if actual_start >= target_level:
                    msg = _('You do not need any combat reports.')
                else:
                    color = SUCCESS_COLOR
                    start_exp = DBMAN.exp_from_level(actual_start) + left_over
                    if target_level > 100:
                        target_exp = DBMAN.exp_from_level(100)
                        mod_exp = DBMAN.exp_from_level(target_level) - target_exp
                    else:
                        target_exp = DBMAN.exp_from_level(target_level)
                        mod_exp = 0
                    target_exp += mod_exp // (oath + 1)
                    reports = ceil((target_exp - start_exp) / 3000)
                    msg = _(f'At **level {actual_start}@({left_over} EXP)**, to reach **level {target_level}** '
                            f'you will need **{reports}** combat reports to cover {target_exp - start_exp} EXP.')
        embed = Embed(color=color, description=msg)
        await ctx.send(embed=embed)

    @commands.command(help='Have Helian lookup T-Doll information by name.')
    async def dinfo(self, ctx: Context, doll: str):
        dolls = DBMAN.tdoll_from_name(f'%{doll}%')
        if dolls is None or not dolls:
            await ctx.send(_('There are no T-Dolls under this alias.'))
        else:
            messages = await self._gen_doll_info_msgs(await LANGMAN.get_lang(ctx), *dolls)
            await _paginate(self.bot, ctx, ctx.author, messages)

    @commands.command(aliases=['rand'],
                      help=_('Have Helian select a random T-Doll.'))
    async def random(self, ctx: Context):
        doll = DBMAN.random_doll()
        messages = await self._gen_doll_info_msgs(await LANGMAN.get_lang(ctx), doll)
        await _paginate(self.bot, ctx, ctx.author, messages)


class Fun(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=['av'],
                      help=_('Have Helian retrieve a user\'s avatar.'))
    async def avatar(self, ctx: Context, user: Optional[Member] = None):
        msg = Embed(color=SUCCESS_COLOR)
        if user is None:
            msg.title = ctx.author.display_name
            msg.set_image(url=ctx.author.avatar_url)
        elif isinstance(user, Member):
            msg.title = user.display_name
            msg.set_image(url=user.avatar_url)
        else:
            raise ValueError
        await ctx.send(embed=msg)

    @commands.command(aliases=['ch'],
                      help=_('Have Helian choose something for you.'))
    async def choose(self, ctx: Context, *content: str):
        if not content:
            await ctx.send(_('Please supply a non-empty comma-separated list.'))
        else:
            await ctx.send(choice(content))

    @commands.is_owner()
    @commands.command(help=_('Have Helian IDW someone.'))
    async def idw(self, ctx: Context, user: Optional[Member] = None):
        if user is None:
            v = ctx.author.voice
        else:
            v = user.voice

        if v is None:
            await ctx.send(_('Please mention a member currently in voice.'))
        else:
            c: VoiceChannel = v.channel
            vc: VoiceClient = await c.connect()
            vc.play(FFmpegPCMAudio('assets/sound/IDW_GAIN_JP.mp3'))
            while vc.is_playing():
                await asyncio.sleep(1)
            vc.stop()
            await vc.disconnect()

    @commands.is_owner()
    @commands.command(aliases=['s'],
                      help=_('Make Helian say something.'))
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
