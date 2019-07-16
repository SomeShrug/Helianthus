import os
import sys

if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.join(path, 'src'))
    import bot

    bot.main()
