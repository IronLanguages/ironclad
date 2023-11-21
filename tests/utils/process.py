
import os
import re


def spawn(executable, *args, **kwargs):
    # Hack for dotnet tool ironpython.console
    # https://github.com/IronLanguages/ironpython3/issues/1756
    executable = re.sub(r"\\\.store\\ironpython\.console\\.+\\ipy\.dll", r"\\ipy.exe", executable)

    cwd = kwargs.get('cwd')
    oldCwd = os.getcwd()
    if cwd:
        os.chdir(cwd)
    try:
        result = os.spawnl(os.P_WAIT, executable, executable, *args)
    finally:
        os.chdir(oldCwd)
    return result

