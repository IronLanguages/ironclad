###############################################################################
#### initialise mapper

__version__ = '0.8.5'

import sys
if sys.platform != 'cli':
    raise ImportError("If you're running CPython, you don't need ironclad. If you're running Jython, ironclad won't work.")

import os
_dirname = os.path.dirname(__file__)

import clr
from System import GC, Int32, IntPtr
from System.Reflection import Assembly
from System.Runtime.InteropServices import Marshal

if Marshal.SizeOf(Int32) != Marshal.SizeOf(IntPtr):
    raise ImportError("Ironclad is currently 32-bit only")

clr.AddReference(Assembly.LoadFile(os.path.join(_dirname, "ironclad.dll")))
from Ironclad import CPyMarshal, Python25Mapper
from Ironclad.Structs import PyObject, PyVarObject, PyTypeObject
_mapper = Python25Mapper(os.path.join(_dirname, "python25.dll"))

def gcwait():
    _mapper.ForceCleanup()
    GC.WaitForPendingFinalizers()

import atexit
def _shutdown():
    try:
        _mapper.Dispose()
        _patch_lifetime._unpatch_all()
    except Exception, e:
        print 'error on ironclad shutdown:'
        print e
    gcwait()
atexit.register(_shutdown)

def shutdown():
    print 'shutdown no longer does anything'

###############################################################################
#### basic attempt to respect .pth files

extrapaths = []
for path in sys.path:
    _, __, filenames = os.walk(path).next()
    for filename in filenames:
        if filename.endswith('.pth'):
            f = open(os.path.join(path, filename))
            for newpath in map(str.strip, f.readlines()):
                newpath = os.path.normpath(os.path.join(path, newpath))
                if os.path.exists(newpath):
                    extrapaths.append(newpath)
            f.close()
sys.path.extend(extrapaths)

###############################################################################
#### native fileno patches

file = _mapper.CPyFileClass
def open(*args):
    return file(*args)

class NativeFilenoPatch(object):
    
    def __init__(self):
        self._count = 0
        self._patches = []
    
    def _apply_patch(self, modname, name, value):
        oldvalue = getattr(sys.modules[modname], name)
        setattr(sys.modules[modname], name, value)
        return (modname, name, oldvalue)

    def _patch_all(self):
        patch = lambda *args: self._patches.append(self._apply_patch(*args))
        patch('__builtin__', 'open', open)
        patch('__builtin__', 'file', _mapper.CPyFileClass)
        
        import os, posix
        for name in 'close fdopen fstat open read tmpfile write'.split():
            patch('os', name, getattr(posix, name))
    
    def _unpatch_all(self):
        while len(self._patches):
            unpatch = self._patches.pop()
            self._apply_patch(*unpatch)
    
    def patch_filenos(self):
        if self._count == 0:
            self._patch_all()
        self._count += 1
        
    def unpatch_filenos(self):
        self._count -= 1
        if self._count == 0:
            self._unpatch_all()
        if self._count < 0:
            raise Exception("filenos not patched; please don't try to unpatch")

_patch_lifetime = NativeFilenoPatch()
patch_native_filenos = _patch_lifetime.patch_filenos
unpatch_native_filenos = _patch_lifetime.unpatch_filenos

###############################################################################
#### various useful functions

def dump_info(obj, size=None):
    print 
    print 'before storing:'
    _mapper.DumpMappingInfo(id(obj))

    objPtr = _mapper.Store(obj)
    if size is None:
        typePtr = CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type")
        size = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_basicsize")
        itemsize = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_itemsize")
        if itemsize > 0:
            itemcount = CPyMarshal.ReadIntField(objPtr, PyVarObject, "ob_size")
            size += itemcount * itemsize
    print 
    print 'after storing:'
    print 'dumping %d bytes of object at %x' % (size, objPtr)
    CPyMarshal.Log(objPtr, size)
    print
    _mapper.DecRef(objPtr)

def set_gc_threshold(value):
    _mapper.GCThreshold = value

def get_gc_threshold():
    return _mapper.GCThreshold

def set_log_errors(value):
    _mapper.LogErrors = value

def get_log_errors():
    return _mapper.LogErrors
    
