import os
import sys
import clr

_dirname = os.path.dirname(__file__)

from System.Reflection import Assembly
clr.AddReference(Assembly.LoadFile(os.path.join(_dirname, "ironclad.dll")))

from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject
_mapper = Python25Mapper(os.path.join(_dirname, "python25.dll"))

def dump(obj, size=None):
    objPtr = _mapper.Store(obj)
    typePtr = CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type")
    if size is None:
        size = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_basicsize")
    print
    print 'dumping %d bytes of object at %x' % (size, objPtr)
    CPyMarshal.Log(objPtr, size)
    print
    _mapper.DecRef(objPtr)

def shutdown():
    _mapper.Dispose()
