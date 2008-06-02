import os
_dirname = os.path.dirname(__file__)

import clr
from System.Reflection import Assembly
clr.AddReference(Assembly.LoadFile(os.path.join(_dirname, "ironclad.dll")))
from Ironclad import Python25Mapper
_mapper = Python25Mapper(os.path.join(_dirname, "python25.dll"))

class Importer(object):
    
    def __init__(self, path):
        pass
    
    def find_module(self, fullname, path=None):
        return self

    def load_module(self, fullname):
        return _mapper.Import(fullname)

import sys
for path in sys.path:
    _mapper.AddToPath(path)
sys.path_hooks.append(Importer)
sys.path_importer_cache.clear()

def shutdown():
    _mapper.Dispose()