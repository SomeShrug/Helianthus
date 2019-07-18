import os
import sys

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, path)
    sys.path.insert(1, os.path.join(path, 'src'))
    sys.path.insert(2, os.path.join(path, 'locales'))
    import bot

    bot.main()
