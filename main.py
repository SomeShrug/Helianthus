import os
import sys
from os import path


def main():
    cwd = path.dirname(path.realpath(path.expanduser(__file__)))
    os.chdir(cwd)
    sys.path.insert(0, path.join(cwd, 'helian'))
    import helian

    helian.main()


if __name__ == '__main__':
    main()
