
import os


def spawn(executable, *args):
    return os.spawnl(os.P_WAIT, executable, executable, *args)

