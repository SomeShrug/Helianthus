import asyncio
import copy
import gc
import sys
from typing import Collection, List, Union

import discord
from discord.ext import commands

from core.data import Equipment, Language, TDoll
from core.resource import *
from core.resource import EMOJI_DOWN, EMOJI_LEFT, EMOJI_RIGHT, EMOJI_UP

_ = lambda x: x
del _

COLOR_FAILURE = 0xb71c1c
COLOR_SUCCESS = 0x00c853

EMBED_SUCCESS = discord.Embed(color=COLOR_SUCCESS)
EMBED_FAILURE = discord.Embed(color=COLOR_FAILURE)


# region T-Doll/Equipment


def construct_doll_production_embed(language: Language, doll: TDoll) -> discord.Embed:
    embed = copy.deepcopy(EMBED_SUCCESS)
    try:
        embed.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[::-1][language.value])
    except IndexError:
        embed.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[Language.EN.value])
    embed.add_field(name=_(INFO_TYPE_LBL), value=doll.type)
    embed.add_field(name=_(INFO_PRODUCTION_TIME_LBL), value=doll.build_time)
    embed.add_field(name=_(INFO_RARITY_LBL), value=EMOJI_STAR * doll.rarity)
    embed.set_image(url=doll.image_url)
    return embed


def construct_doll_information_embed(language: Language, doll: TDoll) -> discord.Embed:
    embed = copy.deepcopy(EMBED_SUCCESS)
    try:
        embed.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[::-1][language.value])
    except IndexError:
        embed.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[Language.EN.value])
    embed.add_field(name=_(INFO_TYPE_LBL), value=doll.type)
    embed.add_field(name=_(INFO_PRODUCTION_TIME_LBL), value=doll.build_time)
    embed.add_field(name=_(INFO_RARITY_LBL), value=EMOJI_STAR * doll.rarity)
    embed.add_field(name=_(INFO_ID_LBL), value=str(doll.id), inline=False)
    embed.add_field(name=_(INFO_BUFF_LBL),
                    value=_(INFO_BUFF_STR).format(tiles=doll.buff,
                                                  description=eval(doll.buff_desc)[language.value]),
                    inline=False)
    embed.add_field(name=_(INFO_SKILL_LBL),
                    value=INFO_SKILL_STR.format(name=eval(doll.slname)[language.value],
                                                description=eval(doll.sldesc)[language.value]))
    embed.add_field(name=_(INFO_ARTIST_LBL), value=doll.artist)
    embed.add_field(name=_(INFO_CV_LBL), value=doll.cv)
    embed.set_image(url=doll.image_url)
    return embed


def construct_doll_mod_information_embed(language: Language, doll: TDoll) -> discord.Embed:
    embed = copy.deepcopy(EMBED_SUCCESS)
    try:
        embed.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[::-1][language.value])
    except IndexError:
        embed.add_field(name=_(INFO_NAME_LBL), value=eval(doll.name)[Language.EN.value])
    embed.add_field(name=_(INFO_TYPE_LBL), value=doll.type)
    embed.add_field(name=_(INFO_PRODUCTION_TIME_LBL), value=doll.build_time)
    embed.add_field(name=_(INFO_RARITY_LBL), value=EMOJI_STAR * doll.mod_rarity)
    embed.add_field(name=_(INFO_ID_LBL), value=str(doll.id), inline=False)

    tile_str = doll.mod_tile if doll.mod_tile else doll.buff
    embed.add_field(name=_(INFO_BUFF_LBL),
                    value=INFO_BUFF_STR.format(tiles=tile_str, description=eval(doll.mod_buff)[language.value]),
                    inline=False)

    sl_trans = tuple(map(lambda x: eval(x)[language.value],
                         (doll.mod_s1_name, doll.mod_s1_desc, doll.mod_s2_name, doll.mod_s2_desc)))
    skill_str = '\n'.join([INFO_SKILL_STR.format(name=sl_trans[i],
                                                 description=sl_trans[i + 1]) for i in range(0, 4, 2)])
    embed.add_field(name=_(INFO_SKILLS_LBL), value=skill_str)

    embed.add_field(name=_(INFO_ARTIST_LBL), value=doll.artist)
    embed.add_field(name=_(INFO_CV_LBL), value=doll.cv)
    embed.set_image(url=doll.mod_image_url)
    return embed


def construct_equip_production_embed(language: Language, equipment: Equipment) -> discord.Embed:
    embed = copy.deepcopy(EMBED_SUCCESS)
    embed.add_field(name=_(INFO_NAME_LBL), value=eval(equipment.name)[language.value])
    embed.add_field(name=_(INFO_TYPE_LBL), value=eval(equipment.type)[language.value])
    embed.add_field(name=_(INFO_PRODUCTION_TIME_LBL), value=equipment.time)
    if equipment.rarity is None:
        embed.set_image(url=equipment.image)
    else:
        embed.add_field(name=_(INFO_RARITY_LBL), value=EMOJI_STAR * equipment.rarity)
        embed.set_thumbnail(url=equipment.image)
    return embed


def construct_equip_information_embed(language: Language, equipment: Equipment) -> discord.Embed:
    embed = copy.deepcopy(EMBED_SUCCESS)
    embed.add_field(name=_(INFO_NAME_LBL), value=eval(equipment.name)[language.value])
    embed.add_field(name=_(INFO_TYPE_LBL), value=eval(equipment.type)[language.value])
    embed.add_field(name=_(INFO_PRODUCTION_TIME_LBL), value=equipment.time, inline=False)
    embed.add_field(name=_(INFO_STATS_LBL), value=eval(equipment.stats)[language.value], inline=False)
    if equipment.is_fairy:
        embed.add_field(name=_(INFO_SKILL_LBL),
                        value=INFO_SKILL_STR.format(name=eval(equipment.slname)[language.value],
                                                    description=eval(equipment.sldesc)[language.value]))
        embed.set_image(url=equipment.image)
    else:
        embed.set_thumbnail(url=equipment.image)
    return embed


def batch_doll_production_embeds(language: Language, *dolls: TDoll) -> List[discord.Embed]:
    add_page_counter = len(dolls) > 1
    embeds = (construct_doll_production_embed(language, doll) for doll in dolls)
    if add_page_counter:
        counters = (_(INFO_PAGE_COUNTER_STR).format(current=page, max=len(dolls))
                    for page in range(1, len(dolls) + 1))
        embeds = map(lambda embed, counter: embed.set_footer(text=counter), embeds, counters)
    return list(embeds)


def batch_equip_production_embeds(language: Language, *equipment: Equipment) -> List[discord.Embed]:
    add_page_counter = len(equipment) > 1
    embeds = (construct_equip_production_embed(language, equip) for equip in equipment)
    if add_page_counter:
        counters = (_(INFO_PAGE_COUNTER_STR).format(current=page, max=len(equipment))
                    for page in range(1, len(equipment) + 1))
        embeds = map(lambda embed, counter: embed.set_footer(text=counter), embeds, counters)
    return list(embeds)


# endregion

# region Miscellaneous

def construct_statistic_embed(language: Language, bot: commands.Bot):
    memory_usage = sum(map(sys.getsizeof, gc.get_objects())) / 1000000
    n_servers = len(bot.guilds)
    channels = bot.get_all_channels()
    channel_count = tuple(map(sum, zip(*((type(chan) is discord.VoiceChannel, type(chan) is discord.TextChannel)
                                         for chan in channels))))
    n_text, n_voice = channel_count
    invite = STATS_INVITE_URL_STR.format(id=bot.user.id)

    embed = copy.deepcopy(EMBED_SUCCESS)
    owner = bot.get_user(bot.owner_id)
    embed.add_field(name=_(STATS_DEVELOPER_LBL), value=f'{owner.display_name}#{owner.discriminator}')
    embed.add_field(name=_(STATS_DEVELOPER_ID_LBL), value=owner.id)
    embed.add_field(name=_(STATS_BOT_ID_LBL), value=bot.user.id)

    embed.add_field(name=_(STATS_MEMORY_USAGE_LBL), value=_(STATS_MEMORY_USAGE_STR.format(memory=memory_usage)))
    embed.add_field(name=_(STATS_PRESENCE_LBL), value=_(STATS_PRESENCE_STR).format(n_servers=n_servers,
                                                                                   n_text=n_text,
                                                                                   n_voice=n_voice))
    embed.add_field(name=_(STATS_LANGUAGE_LBL), value=language.name)
    embed.add_field(name=_(STATS_INVITE_LBL), value=invite)
    return embed


# endregion


async def paginate(bot: commands.Bot,
                   ctx: commands.Context,
                   target: discord.Member,
                   messages: Union[List[discord.Embed], List[List[discord.Embed]]]):
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

            def check(r: discord.Reaction, u: discord.Member) -> bool:
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
