import sys

is_ironpython =  sys.implementation.name == 'ironpython'
is_cpython    =  sys.implementation.name == 'cpython'
is_windows    =  sys.platform == 'win32'
is_linux      =  sys.platform == 'linux'
is_osx        =  sys.platform == 'darwin'
is_posix      =  is_linux or is_osx

is_netcoreapp = False
if is_ironpython:
    import clr
    is_netcoreapp = clr.IsNetCoreApp