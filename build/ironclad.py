import os
_dirname = os.path.dirname(__file__)

import clr
from System.Reflection import Assembly
clr.AddReference(Assembly.LoadFile(os.path.join(_dirname, "ironclad.dll")))
from Ironclad import Python25Mapper
_mapper = Python25Mapper(os.path.join(_dirname, "python25.dll"))
clr.AddReference('IronPython')
from IronPython.Hosting import Python
_other_sys = Python.GetSysModule(_mapper.Engine)

class Importer(object):
    
    def __init__(self, path):
        pass
    
    def find_module(self, fullname, path=None):
        return self

    def load_module(self, fullname):
        _mapper.Import(fullname)
        dotted = fullname + '.'
        for name, module in _other_sys.modules.items():
            if name == fullname or name.startswith(dotted):
                sys.modules[name] = module
        return sys.modules[fullname]
        

import sys
sys.path_hooks.append(Importer)
sys.path_importer_cache.clear()

# required for numpy; should be fixed in ipy at some point
sys.__displayhook__ = sys.displayhook

def shutdown():
    _mapper.Dispose()
