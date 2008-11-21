import os
import sys
import clr

_dirname = os.path.dirname(__file__)

from System.Reflection import Assembly
clr.AddReference(Assembly.LoadFile(os.path.join(_dirname, "ironclad.dll")))

from Ironclad import Python25Mapper
_mapper = Python25Mapper(os.path.join(_dirname, "python25.dll"))

def shutdown():
    _mapper.Dispose()
