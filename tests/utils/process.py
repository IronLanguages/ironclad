
import os


def spawn(executable, *args, **kwargs):
    cwd = kwargs.get('cwd')
    oldCwd = os.getcwd()
    if cwd:
        os.chdir(cwd)
    try:
        result = os.spawnl(os.P_WAIT, executable, executable, *args)
    finally:
        os.chdir(oldCwd)
    return result

