import os
import sys
from os import path

if __name__ == '__main__':
    cwd = path.dirname(path.realpath(path.expanduser(__file__)))
    os.chdir(cwd)
    sys.path.insert(0, path.join(cwd, 'src'))
    import bot

    bot.main()
