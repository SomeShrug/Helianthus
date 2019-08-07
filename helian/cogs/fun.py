import asyncio
import random
from typing import Optional

import discord
from discord.ext import commands

from core.resource import *

_ = lambda x: x
del _


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['av'], help=_(CMD_AVATAR_HELP_STR))
    async def avatar(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        msg = discord.Embed(color=SUCCESS_COLOR)
        if user is None:
            msg.title = f'{ctx.author.name}#{ctx.author.discriminator}'
            msg.set_image(url=ctx.author.avatar_url)
        elif isinstance(user, discord.Member):
            msg.title = f'{user.name}#{user.discriminator}'
            msg.set_image(url=user.avatar_url)
        await ctx.send(embed=msg)

    @commands.command(aliases=['ch'], help=_(CMD_CHOOSE_HELP_STR))
    async def choose(self, ctx: commands.Context, *content: str):
        if not all(content):
            await ctx.send(_(CMD_CHOOSE_EMPTY_INPUT_STR))
        else:
            await ctx.send(random.choice(content))

    @commands.is_owner()
    @commands.command(help=_(CMD_IDW_HELP_STR))
    async def idw(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        if user is None:
            v = ctx.author.voice
        else:
            v = user.voice

        if v is None:
            await ctx.send(_(CMD_IDW_MENTION_NOT_IN_VOICE_STR))
        else:
            c: discord.VoiceChannel = v.channel
            vc: discord.VoiceClient = await c.connect()
            vc.play(discord.FFmpegPCMAudio('assets/sound/IDW_GAIN_JP.ogg'))
            while vc.is_playing():
                await asyncio.sleep(1)
            vc.stop()
            await vc.disconnect()

    @commands.is_owner()
    @commands.command(aliases=['s'], help=_(CMD_SAY_HELP_STR))
    async def say(self, ctx: commands.Context, *, content: str):
        await ctx.message.delete()
        await ctx.send(content)
