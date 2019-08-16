import asyncio
import copy
import itertools
import math
from typing import List, Optional

from discord import Embed, Message
from discord.ext import commands

from core.data import DBMAN, Language, SETMAN, TDoll
from core.embed import batch_doll_production_embeds, batch_equip_production_embeds, construct_doll_information_embed, \
    construct_equip_information_embed, paginate
from core.resource import *
from core.utility import sanitize_time, similar

# noinspection PyPep8
_ = lambda x: x
del _


class Analytics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
                mod = copy.deepcopy(embed)
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
                page_ctr = _(INFO_PAGE_COUNTER_STR).format(current=page, max=len(dolls))
                if doll.mod_rarity and mod is not None:
                    footer = INFO_FOOTER_STR.format(page=page_ctr,
                                                    sub_page=_(INFO_SUBPAGE_COUNTER_STR).format(current=1,
                                                                                                max=2))
                    mod_footer = INFO_FOOTER_STR.format(page=page_ctr,
                                                        sub_page=_(INFO_SUBPAGE_COUNTER_STR).format(current=2,
                                                                                                    max=2))
                    mod.set_footer(text=mod_footer)
                else:
                    footer = INFO_FOOTER_STR.format(page=page_ctr, sub_page='')
                embed.set_footer(text=footer)

            sub_pages.append(embed)
            if mod is not None:
                sub_pages.append(mod)

            embeds.append(sub_pages)

        return embeds

    @commands.command(name='doll', aliases=['d'], help=_(CMD_DOLL_HELP_STR))
    async def get_tdoll_from_time(self, ctx: commands.Context, prod_time: str):
        prod_time = sanitize_time(prod_time)
        if prod_time is None:
            await ctx.send(_(TIME_FORMAT_ERROR_STR))
            return
        dolls = DBMAN.tdoll_from_time(prod_time)
        embeds = batch_doll_production_embeds(await SETMAN.get_lang(ctx), *dolls)

        if len(dolls) > 1:
            await paginate(self.bot, ctx, ctx.author, embeds)
        elif dolls:
            await ctx.send(embed=embeds.pop())
        else:
            await ctx.send(_(CMD_DOLL_DOLL_NOT_FOUND_STR))

    @commands.command(name='equip', aliases=['e'], help=_(CMD_EQUIP_HELP_STR))
    async def get_equipment_from_time(self, ctx: commands.Context, production_time: str):
        production_time = sanitize_time(production_time)
        if production_time is None:
            await ctx.send(_(TIME_FORMAT_ERROR_STR))
            return
        equipment = DBMAN.equip_from_time(production_time)
        embeds = batch_equip_production_embeds(await SETMAN.get_lang(ctx), *equipment)
        if len(equipment) > 1:
            await paginate(self.bot, ctx, ctx.author, embeds)
        elif equipment:
            await ctx.send(embed=embeds[-1])
        else:
            await ctx.send(_(CMD_EQUIP_EQUIP_NOT_FOUND_STR))

    @commands.command(name='fexp', help=_(CMD_FEXP_HELP_STR))
    async def get_fairy_combat_reports(self,
                                       ctx: commands.Context,
                                       start_level: int,
                                       exp: int,
                                       target_level: int):
        color = FAIL_COLOR
        if not 1 <= start_level <= 100:
            msg = _(CMD_FEXP_INVALID_START_LEVEL_STR)
        elif not 1 <= target_level <= 100:
            msg = _(CMD_FEXP_INVALID_TARGET_LEVEL_STR)
        elif target_level <= start_level:
            msg = _(CMD_FEXP_TARGET_LESS_THAN_START_STR).format(level=start_level)
        else:
            start_exp = DBMAN.exp_from_level(start_level, True)
            start_exp += exp
            try:
                actual_start, left_over = DBMAN.level_from_exp(start_exp, True)

            except ValueError:
                msg = _(CMD_EXP_INVALID_EXP_STR)
            else:
                if actual_start >= target_level:
                    msg = _(CMD_EXP_REPORT_UNNCESSARY_STR)
                else:
                    color = SUCCESS_COLOR
                    actual_exp = DBMAN.exp_from_level(actual_start, True) + left_over
                    target_exp = DBMAN.exp_from_level(target_level, True)

                    exp_diff = (target_exp - actual_exp)
                    reports = math.ceil(exp_diff / 3000)
                    msg = _(CMD_FEXP_OUTPUT_STR).format(start=actual_start,
                                                        exp=left_over,
                                                        target=target_level,
                                                        reports=reports,
                                                        exp_difference=exp_diff)
        embed = Embed(color=color, description=msg)
        await ctx.send(embed=embed)

    @commands.command(help=_(CMD_EXP_HELP_STR))
    async def exp(self,
                  ctx: commands.Context,
                  start_level: int,
                  exp: int,
                  target_level: int,
                  oath: Optional[bool] = False):

        color = FAIL_COLOR
        if not 1 <= start_level <= 120:
            msg = _(CMD_EXP_INVALID_START_LEVEL_STR)
        elif not 1 <= target_level <= 120:
            msg = _(CMD_EXP_INVALID_TARGET_LEVEL_STR)
        elif target_level <= start_level:
            msg = _(CMD_EXP_TARGET_LESS_THAN_START_STR).format(level=start_level)
        else:
            start_exp = DBMAN.exp_from_level(start_level)
            start_exp += exp
            try:
                actual_start, left_over = DBMAN.level_from_exp(start_exp)
                print(actual_start)

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
                    reports = math.ceil(exp_diff / 3000)
                    msg = _(CMD_EXP_OUTPUT_STR).format(start=actual_start,
                                                       exp=left_over,
                                                       target=target_level,
                                                       reports=reports,
                                                       exp_difference=exp_diff)
        embed = Embed(color=color, description=msg)
        await ctx.send(embed=embed)

    @commands.command(help=_(CMD_INFO_HELP_STR))
    async def info(self, ctx: commands.Context, alias: str):
        dolls = DBMAN.tdoll_from_name(DB_ALIAS_STR.format(alias=alias))
        equipment = DBMAN.equip_from_name(DB_ALIAS_STR.format(alias=alias))

        if len(tuple(itertools.chain(dolls, equipment))) > 50:
            await ctx.send(_(CMD_INFO_BROAD_SEARCH_STR))
        elif dolls is None and equipment is None or not dolls and not equipment:
            await ctx.send(_(CMD_INFO_ENTITY_NOT_FOUND_STR))
        else:
            lang = (await SETMAN.get_lang(ctx))
            try:
                if dolls:
                    _(eval(dolls[0].name)[::-1][lang.value])
                else:
                    _(eval(equipment[0].name)[lang.value])
            except IndexError:
                lang = Language.EN
            fairies = list(filter(lambda x: x.is_fairy, equipment))
            equipment = list(filter(lambda x: not x.is_fairy, equipment))

            diff_key = lambda x: max(map(lambda y: similar(y, alias.lower()), case_key(x).split()))
            case_key = lambda x: eval(x.name)[::-1][lang.value].lower()

            unfiltered = (dolls, equipment, fairies)
            results = [sorted(sorted(pool, key=case_key), key=diff_key, reverse=True) for pool in unfiltered]
            search_list = tuple(itertools.chain.from_iterable(results))
            search_list = sorted(sorted(search_list, key=case_key), key=diff_key, reverse=True)

            if len(search_list) > 1:
                get_qualified_type = lambda entity: 'TDOLL' if type(entity) is TDoll else (
                    'FAIRY' if entity.is_fairy else 'EQUIPMENT')
                get_name = lambda entity: eval(entity.name)[::(type(entity) is not TDoll) * 2 - 1][lang.value]
                entries = [f'[{idx:>2}] [{get_qualified_type(entity):^9}] {get_name(entity)}' for idx, entity in
                           enumerate(search_list)]
                out_str = "\n".join(entries)

                select_msg = await ctx.send(f'```{_(CMD_INFO_SELECT_ENTITY_STR)}\n\n{out_str}```')

                def number_check(s: Message):
                    return s.clean_content.isdigit() and 0 <= int(s.clean_content) <= len(search_list)

                try:
                    selection = await self.bot.wait_for('message', check=number_check, timeout=20.0)
                except asyncio.TimeoutError:
                    result = None
                else:
                    result = search_list[int(selection.clean_content)]
                finally:
                    await select_msg.delete()
            else:
                result = search_list[-1]

            if result is None:
                return

            if type(result) == TDoll:
                embed = construct_doll_information_embed(lang, result)
            else:
                embed = construct_equip_information_embed(lang, result)
            await ctx.send(embed=embed)

    @commands.command(name='dinfo', help=_(CMD_DEPRECATED_STR))
    async def dinfo_deprecation_warning(self, ctx: commands.Context):
        raise DeprecationWarning(self.info)

    @commands.command(aliases=['rand'], help=_(CMD_RANDOM_HELP_STR))
    async def random(self, ctx: commands.Context):
        doll = DBMAN.random_doll()
        messages = await self._gen_doll_info_msgs(await SETMAN.get_lang(ctx), doll)
        await paginate(self.bot, ctx, ctx.author, messages)


def setup(bot: commands.Bot) -> None:
    if Analytics.__name__ in bot.cogs.keys():
        bot.remove_cog(Analytics.__name__)
