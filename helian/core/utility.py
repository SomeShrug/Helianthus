import difflib
from typing import Optional

from core.data import TIME_REGEX


def sanitize_time(s: str) -> Optional[str]:
    m = TIME_REGEX.search(s)
    if m is None:
        return None
    csep, nosep = m.group(1, 2)
    if csep is not None:
        out = map(lambda i: i.zfill(2), csep.split(':'))
    else:
        temp = nosep.zfill(4)
        out = (temp[:2], temp[2:])
    return ':'.join(out)


def similar(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def mono(s: str):
    return f'`{s}`'


def code(s: str):
    return f'```{s}```'


def bold(s: str):
    return f'**{s}**'


def italic(s: str):
    return f'*{s}*'


def spoiler(s: str):
    return f'||{s}||'


def strike(s: str):
    return f'~~{s}~~'
