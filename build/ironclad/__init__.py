###############################################################################
#### initialise mapper

__version__ = '2.7.0A1'

import sys
if sys.platform != 'cli':
    raise ImportError("If you're running CPython, you don't need ironclad. If you're running Jython, ironclad won't work.")

import os
_dirname = os.path.dirname(__file__)

import clr
from System import GC, Int64, IntPtr
from System.Reflection import Assembly
from System.Runtime.InteropServices import Marshal

if Marshal.SizeOf(Int64()) != Marshal.SizeOf(IntPtr()):
    raise ImportError("Ironclad is currently 64-bit only")

clr.AddReference(Assembly.LoadFile(os.path.join(_dirname, "ironclad.dll")))
from Ironclad import CPyMarshal, PythonMapper
from Ironclad.Structs import PyObject, PyVarObject, PyTypeObject
_mapper = PythonMapper(os.path.join(_dirname, "python27.dll"))

def gcwait():
    """
    Attempt to force a garbage collection, and wait for pending finalizers.
    
    If you think you need to call this function, you're probably wrong.
    """
    for _ in range(4):
        _mapper.DemandCleanup()
        GC.Collect()
        GC.WaitForPendingFinalizers()

import atexit
def _shutdown():
    try:
        _mapper.Dispose()
        _patch_lifetime._unpatch_all()
    except Exception, e:
        print 'error on ironclad shutdown:'
        print e
    # gcwait's docstring still applies; its only value is to (hopefully) induce
    # shutdown crashes *now*, rather than later, so you have a chance of figuring
    # out their source. mostly useful for functional tests.
    gcwait()
atexit.register(_shutdown)

def shutdown():
    print 'shutdown no longer does anything'

###############################################################################
#### basic attempt to respect .pth files

extrapaths = []
for path in sys.path:
    if not os.path.isdir(path):
        continue
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
#### native fileno patches (optional)

file = _mapper.CPyFileClass
def open(*args, **kwargs):
    return file(*args, **kwargs)

class _NativeFilenoPatch(object):
    
    def __init__(self):
        self._count = 0
        self._patches = []
    
    def _apply_patch(self, modname, name, value):
        oldvalue = getattr(sys.modules[modname], name)
        setattr(sys.modules[modname], name, value)
        return (modname, name, oldvalue)

    def _patch_all(self):
        oldopen = sys.modules['__builtin__'].open
        
        patch = lambda *args: self._patches.append(self._apply_patch(*args))
        patch('__builtin__', 'open', open)
        patch('__builtin__', 'file', _mapper.CPyFileClass)
        
        import os, posix
        for name in 'close fdopen fstat open read tmpfile write'.split():
            patch('os', name, getattr(posix, name))
        
        # using cpy files with linecache generates too much noise when
        # trying to figure out failing tests for scipy (et al)
        import linecache
        linecache.open = oldopen
    
    def _unpatch_all(self):
        while len(self._patches):
            unpatch = self._patches.pop()
            self._apply_patch(*unpatch)
    
    def patch_filenos(self):
        """
        Replace IronPython's builtin 'file' and 'open' with the CPython implementations; also patch
        functions in the os module which expect a fileno which corresponds to an OS file descriptor.
        This is necessary if you want to use the 'mmap' module, or anything which depends on it, 
        inclding parts of numpy and scipy.
        """
        if self._count == 0:
            self._patch_all()
        self._count += 1
        
    def unpatch_filenos(self):
        """
        Undo the effects of patch_native_filenos. Be aware that live code may still reference
        CPython's 'file' and 'open', so it's probably best to decide what you want and stick 
        with it.
        """
        self._count -= 1
        if self._count == 0:
            self._unpatch_all()
        if self._count < 0:
            raise Exception("filenos not patched; please don't try to unpatch them")

_patch_lifetime = _NativeFilenoPatch()
patch_native_filenos = _patch_lifetime.patch_filenos
unpatch_native_filenos = _patch_lifetime.unpatch_filenos

###############################################################################
#### various useful functions

def log_info(obj, size=None):
    """
    Print useful debugging information about the first argument.
    Optional second argument allows you to specify how many bytes of the object's
    unmanaged representation to print; it is not generally useful or wise to make
    use of it.
    """
    print 
    print 'before storing:'
    _mapper.LogMappingInfo(id(obj))

    print 
    print 'after storing:'
    objPtr = _mapper.Store(obj)
    if size is None:
        typePtr = CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type")
        size = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_basicsize")
        itemsize = CPyMarshal.ReadIntField(typePtr, PyTypeObject, "tp_itemsize")
        if itemsize > 0:
            itemcount = CPyMarshal.ReadIntField(objPtr, PyVarObject, "ob_size")
            size += itemcount * itemsize
    print 'printing %d bytes of object at %x' % (size, objPtr)
    CPyMarshal.Log(objPtr, size)
    print
    _mapper.DecRef(objPtr)

def log_refs():
    """
    Print useful debugging information about the state of Ironclad's internal object
    mapping.
    """
    _mapper.LogRefs()

def set_gc_threshold(value):
    """
    Set how frequently Ironclad performs tedious bookkeeping tasks. The default value of
    50,000 gives decent performance at the cost of a noticeably sawtoothed memory usage 
    graph when lots of objects are being created and destroyed; if you find yourself 
    running out of memory, you may want to reduce this value.
    
    For reference, a value of 500 produces a near-enough-flat memory usage graph, with 
    *average* performance degradation of approximately 50%; however, in the worst case, 
    the degradation is really really awful, so treat it with some respect.
    
    Increasing the value to 5,000,000 produces a performance benefit of maybe 8% on a good 
    day, and probably isn't worth bothering with, but certain applications could benefit
    noticeably. YMMV.
    """
    _mapper.GCThreshold = value

def get_gc_threshold():
    """
    Get the current GC threshold value. See set_gc_threshold docstring for a vague
    discussion of what this means, and why you might care about it.
    """
    return _mapper.GCThreshold

def set_log_errors(value):
    """
    Spam stdout with an unimaginably vast quantity of pointless information. Even if
    you're actively developing Ironclad, this is very rarely worth it, but it still 
    exists because it's tedious to rewrite the code on the rare occasions it is useful.
    
    May also be handy for stack trace fetishists without internet access.
    """
    _mapper.LogErrors = value

def get_log_errors():
    """If this function returns True, just call set_log_errors(False). Really."""
    return _mapper.LogErrors
    
