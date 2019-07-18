import dataclasses
import enum
import gettext
import json
import re
import sqlite3
from itertools import takewhile
from typing import Collection, List, Optional

from discord.ext.commands import Context

# TODO: Axe all of this for GFDB :3
from resources import APP_DOMAIN, DB_EQUIPMENT_TIME_QUERY, DB_TDOLL_NAME_QUERY, DB_TDOLL_RANDOM_QUERY, \
    DB_TDOLL_TIME_QUERY

TIME_REGEX = re.compile(r'''^(\d{1,2}:\d{1,2})$|^(\d{1,4})$''')


async def _format_time(s: str) -> Optional[str]:
    m = TIME_REGEX.search(s)
    if m is None:
        return None
    csep, nosep = m.group(1, 2)
    if csep is not None:
        return ':'.join(map(lambda i: i.zfill(2), csep.split(':')))
    else:
        temp = nosep.zfill(4)
        return ':'.join((temp[:2], temp[2:]))


class Language(enum.Enum):
    KO = 0
    EN = 1
    JP = 2

    @staticmethod
    def is_lang(lang: str) -> bool:
        return lang.upper() in Language.__members__


class ProductionType(enum.IntFlag):
    DOLL = 0x1
    EQUIPMENT = 0x2
    FAIRY = 0x4


@dataclasses.dataclass()
class TDoll(object):
    id: int = 0
    name: str = ''
    build_time: str = ''
    type: str = ''
    rarity: int = 0
    image: str = ''
    buff: str = ''
    buff_desc: str = ''
    slname: str = ''
    sldesc: str = ''
    artist: str = ''
    cv: str = ''
    alias: str = ''
    buff_to: str = ''
    mod_s1_name: str = ''
    mod_s1_desc: str = ''
    mod_s2_name: str = ''
    mod_s2_desc: str = ''
    mod_buff: str = ''
    mod_image: str = ''
    mod_rarity: int = 0
    mod_tile: str = ''


@dataclasses.dataclass()
class Equipment(object):
    time: str = ''
    name: str = ''
    rarity: int = 0
    type: str = ''
    stats: str = ''
    image: str = ''
    slname: str = ''
    sldesc: str = ''


DEFAULT_LANGUAGE = Language.EN


# TODO: Use gettext instead of this
class SettingsManager(object):
    def __init__(self):
        self._stbl = None
        self._strtbl = None
        self._languages = dict.fromkeys(Language.__members__.values())
        with open('assets/lang.json', 'r+', encoding='utf8') as f:
            self._stbl = json.load(f)
        gettext.install(APP_DOMAIN, 'locales')
        for language in Language.__members__.values():
            self._languages[language] = gettext.translation(APP_DOMAIN,
                                                            localedir='locales',
                                                            languages=[language.name.lower(), ])

    async def reload(self) -> None:
        with open('assets/lang.json', 'r+', encoding='utf8') as f:
            self._stbl = json.load(f)

    async def install_lang(self, ctx: Context):
        self._languages[await self.get_lang(ctx)].install()

    async def get_lang(self, ctx: Context) -> Language:
        s_id = str(ctx.guild.id)
        c_id = str(ctx.channel.id)
        if s_id in self._stbl:
            s = self._stbl[s_id]
            try:
                if c_id in s['channels']:
                    lang = s['channels'][c_id]
                else:
                    lang = s['lang']
                return Language[lang]
            except KeyError:
                return Language[s['lang']]
        else:
            return DEFAULT_LANGUAGE

    async def set_slang(self, ctx: Context, lang: str) -> None:
        lang = lang.upper()
        if lang not in Language.__members__:
            raise ValueError('Invalid language')
        s_id = str(ctx.guild.id)
        self._stbl.setdefault(s_id, {})
        self._stbl[s_id]['lang'] = lang
        await self.dump()

    async def set_chlang(self, ctx: Context, lang: str) -> None:
        lang = lang.upper()
        if lang not in Language.__members__:
            raise ValueError('Invalid language')
        s_id = str(ctx.guild.id)
        c_id = str(ctx.channel.id)
        self._stbl.setdefault(s_id, {'lang': lang})
        self._stbl[s_id].setdefault('channels', {})
        self._stbl[s_id]['channels'][c_id] = lang
        await self.dump()

    async def del_chlang(self, ctx: Context) -> None:
        try:
            print(self._stbl[str(ctx.guild.id)]['channels'][str(ctx.channel.id)])
            del self._stbl[str(ctx.guild.id)]['channels'][str(ctx.channel.id)]
        except KeyError:
            raise KeyError
        await self.dump()

    async def dump(self):
        with open('assets/lang.json', 'w', encoding='utf8') as f:
            json.dump(self._stbl, f, indent=2, sort_keys=True)


class DatabaseManager(object):
    def __init__(self):
        self._db = sqlite3.connect('db/helian.db')
        self._c = self._db.cursor()

        with open('assets/exp_data.csv') as f:
            self._exp_data = tuple(map(int, f.read().split(',')))

    @property
    def max_level(self):
        return len(self._exp_data)

    def exp_from_level(self, level: int) -> int:
        return self._exp_data[level - 1]

    def level_from_exp(self, exp: int) -> Collection[int]:
        if not 0 <= exp <= self._exp_data[-1]:
            raise ValueError
        temp = tuple(takewhile(lambda x: exp >= x, self._exp_data))
        level = len(temp)
        leftover = exp - temp[-1]
        return level, leftover

    def tdoll_from_time(self, time: str) -> List[TDoll]:
        self._c.execute(DB_TDOLL_TIME_QUERY, (time,))
        data = self._c.fetchall()
        dolls = [TDoll(*row) for row in data]
        return dolls

    def tdoll_from_name(self, name: str) -> List[TDoll]:
        self._c.execute(DB_TDOLL_NAME_QUERY, (name,))
        data = self._c.fetchall()
        dolls = [TDoll(*row) for row in data]
        return dolls

    def equip_from_time(self, time: str) -> List[Equipment]:
        self._c.execute(DB_EQUIPMENT_TIME_QUERY, (time,))
        data = self._c.fetchall()
        equipment = [Equipment(*row) for row in data]
        return equipment

    def random_doll(self) -> TDoll:
        self._c.execute(DB_TDOLL_RANDOM_QUERY)
        data = self._c.fetchone()
        return TDoll(*data)

    def close(self):
        self._c.close()
        self._db.close()


SETMAN = SettingsManager()
DBMAN = DatabaseManager()


def setup(*args):
    del args
    SETMAN.__class__ = SettingsManager
    DBMAN.__class__ = DatabaseManager
    print(f'Loaded {__file__}')
