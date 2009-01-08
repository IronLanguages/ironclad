
import sys
if sys.platform != 'cli':
    raise ImportError("If you're running CPython, you don't need ironclad. If you're running Jython, ironclad won't work.")

import os
_dirname = os.path.dirname(__file__)

import clr
from System import GC
from System.Reflection import Assembly
clr.AddReference(Assembly.LoadFile(os.path.join(_dirname, "ironclad.dll")))

from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject, PyVarObject, PyTypeObject
_mapper = Python25Mapper(os.path.join(_dirname, "python25.dll"))

def shutdown():
    gcwait()
    try:
        _mapper.Dispose()
    except Exception, e:
        print 'error on mapper Dispose:'
        print e
    gcwait()


# various useful functions

def dump(obj, size=None):
    objPtr = _mapper.Store(obj)
    if size is None:
        typePtr = CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type")
        size = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_basicsize")
        itemsize = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_itemsize")
        if itemsize > 0:
            itemcount = CPyMarshal.ReadIntField(objPtr, PyVarObject, "ob_size")
            size += itemcount * itemsize
    print 
    print 'dumping %d bytes of object at %x' % (size, objPtr)
    CPyMarshal.Log(objPtr, size)
    print
    _mapper.DecRef(objPtr)

def set_gc_threshold(value):
    _mapper.GCThreshold = value

def get_gc_threshold():
    return _mapper.GCThreshold

def gcwait():
    GC.Collect()
    GC.WaitForPendingFinalizers()
    
