
def lock(f):
    def locked(*args, **kwargs):
        EnsureGIL();
        try:
            return f(*args, **kwargs)
        finally:
            ReleaseGIL();
    return locked

Null = object()
NullPtr = IntPtr(0)

# Note: you MUST lock around calls into C code, otherwise horrible
# things happen at object deletion time. Bear this in mind when 
# adding new dispatch methods.

class Dispatcher(object):

    def __init__(self, mapper, table):
        self.mapper = mapper
        self.table = table

    def _store(self, obj):
        if obj is Null: return NullPtr
        return self.mapper.Store(obj)

    def _cleanup(self, *args):
        self.mapper.FreeTemps()
        for arg in args:
            if arg != NullPtr:
                self.mapper.DecRef(arg)
        self.mapper.CheckBridgePtrs()

    def _check_error(self):
        error = self.mapper.LastException
        if error:
            self.mapper.LastException = None
            raise error

    def _raise(self, fallbackError):
        self._check_error()
        raise fallbackError

    def _return(self, result=None):
        self._check_error()
        return result

    def _return_retrieve(self, resultPtr):
        self._check_error()
        if resultPtr == NullPtr:
            raise NullReferenceException('CPython callable returned null without setting an exception')
        return self.mapper.Retrieve(resultPtr)
    
    @lock
    def construct(self, name, klass, *args, **kwargs):
        # TODO: yes, I do leak a reference to klass here. proper reference counting 
        # for types will be implemented as soon as it actually breaks something; for
        # now, laziness and short-term sanity-preservation win the day.
        if not kwargs: kwargs = Null
        klassPtr, argsPtr, kwargsPtr = map(self._store, [klass, args, kwargs])
        instancePtr = self.table[name](klassPtr, argsPtr, kwargsPtr)
        try:
            self._check_error()
            return self._return_retrieve(instancePtr)
        finally:
            self._cleanup(instancePtr, argsPtr, kwargsPtr)
        
    @lock
    def init(self, name, instance, *args, **kwargs):
        if not self.table.has_key(name):
            return
        if not kwargs: kwargs = Null
        instancePtr, argsPtr, kwargsPtr = map(self._store, [instance, args, kwargs])
        result = self.table[name](instancePtr, argsPtr, kwargsPtr)
        self._cleanup(instancePtr, argsPtr, kwargsPtr)
        if result < 0:
            self._raise(Exception('%s failed; object is probably not safe to use' % name))
        self._check_error()

    @lock
    def delete(self, instance):
        # note: _store will incref, so we need to decref twice here
        instancePtr = self._store(instance)
        refcnt = self.mapper.RefCount(instancePtr)
        if refcnt != 2:
            print 'eek! deleting object with bad refcount. id: %d, ptr: %s, refcnt: %d' % (
                id(instance), instancePtr.ToString('x'), refcnt)

        self.mapper.DecRef(instancePtr)
        self.mapper.DecRef(instancePtr)
        self.mapper.Unmap(instancePtr)
        self._check_error()

    def dontDelete(self, _):
        pass

    @lock
    def method_getter(self, name, instance, closurePtr):
        instancePtr = self._store(instance)
        resultPtr = self.table[name](instancePtr, closurePtr)
        try:
            return self._return_retrieve(resultPtr)
        finally:
            self._cleanup(instancePtr, resultPtr)

    @lock
    def method_setter(self, name, instance, value, closurePtr):
        instancePtr, valuePtr = map(self._store, [instance, value])
        result = self.table[name](instancePtr, valuePtr, closurePtr)
        self._cleanup(instancePtr, valuePtr)
        if result < 0:
            self._raise(Exception('%s failed' % name))
        self._check_error()
        return self._return()

    def get_member_int(self, instance, offset):
        return self._get_member(instance, offset, 'ReadInt')

    def set_member_int(self, instance, offset, value):
        self._set_member(instance, offset, 'WriteInt', value)

    def get_member_char(self, instance, offset):
        return chr(self._get_member(instance, offset, 'ReadByte'))

    def set_member_char(self, instance, offset, value):
        self._set_member(instance, offset, 'WriteByte', ord(value))

    def get_member_ubyte(self, instance, offset):
        return self._get_member(instance, offset, 'ReadByte')

    def set_member_ubyte(self, instance, offset, value):
        self._set_member(instance, offset, 'WriteByte', value)

    @lock
    def _get_member(self, instance, offset, method):
        instancePtr = self._store(instance)
        address = CPyMarshal.Offset(instancePtr, offset)
        result = getattr(CPyMarshal, method)(address)
        self._cleanup(instancePtr)
        return result

    @lock
    def _set_member(self, instance, offset, method, value):
        instancePtr = self._store(instance)
        address = CPyMarshal.Offset(instancePtr, offset)
        getattr(CPyMarshal, method)(address, value)
        self._cleanup(instancePtr)

    @lock
    def get_member_object(self, instance, offset):
        instancePtr = self._store(instance)
        address = CPyMarshal.Offset(instancePtr, offset)
        valuePtr = CPyMarshal.ReadPtr(address)
        result = None
        if valuePtr != NullPtr:
            result = self.mapper.Retrieve(valuePtr)
            self._store(result)
        self._cleanup(instancePtr)
        return result

    @lock
    def set_member_object(self, instance, offset, value):
        instancePtr, valuePtr = map(self._store, [instance, value])
        address = CPyMarshal.Offset(instancePtr, offset)
        oldValuePtr = CPyMarshal.ReadPtr(address)
        CPyMarshal.WritePtr(address, valuePtr)
        self._cleanup(instancePtr, oldValuePtr)

    def function_noargs(self, name):
        return self._call_O_OO(name, Null, Null)

    def method_noargs(self, name, instance):
        return self._call_O_OO(name, instance, Null)

    def function_objarg(self, name, arg):
        return self._call_O_OO(name, Null, arg)
        
    def method_objarg(self, name, instance, arg):
        return self._call_O_OO(name, instance, arg)

    def function_varargs(self, name, *args):
        return self._call_O_OO(name, Null, args)

    def method_varargs(self, name, instance, *args):
        return self._call_O_OO(name, instance, args)

    def function_kwargs(self, name, *args, **kwargs):
        if not kwargs: kwargs = Null
        return self._call_O_OOO(name, Null, args, kwargs)

    def method_kwargs(self, name, instance, *args, **kwargs):
        if not kwargs: kwargs = Null
        return self._call_O_OOO(name, instance, args, kwargs)

    def method_ternary(self, name, instance, arg1, arg2):
        return self._call_O_OOO(name, instance, arg1, arg2)

    def method_ternary_swapped(self, name, instance, arg):
        return self._call_O_OOO(name, arg, instance, Null)

    @lock
    def _call_O_OO(self, name, arg1, arg2):
        arg1Ptr, arg2Ptr = map(self._store, [arg1, arg2])
        resultPtr = self.table[name](arg1Ptr, arg2Ptr)
        try:
            return self._return_retrieve(resultPtr)
        finally:
            self._cleanup(arg1Ptr, arg2Ptr, resultPtr)

    @lock
    def _call_O_OOO(self, name, arg1, arg2, arg3):
        arg1Ptr, arg2Ptr, arg3Ptr = map(self._store, [arg1, arg2, arg3])
        resultPtr = self.table[name](arg1Ptr, arg2Ptr, arg3Ptr)
        try:
            return self._return_retrieve(resultPtr)
        finally:
            self._cleanup(arg1Ptr, arg2Ptr, arg3Ptr, resultPtr)
    
    @lock
    def method_selfarg(self, name, instance, errorHandler=None):
        instancePtr = self._store(instance)
        resultPtr = self.table[name](instancePtr)
        try:
            if errorHandler: errorHandler(resultPtr)
            return self._return_retrieve(resultPtr)
        finally:
            self._cleanup(instancePtr, resultPtr)

    @lock
    def method_ssizearg(self, name, instance, i):
        instancePtr = self._store(instance)
        resultPtr = self.table[name](instancePtr, i)
        try:
            return self._return_retrieve(resultPtr)
        finally:
            self._cleanup(instancePtr, resultPtr)

    @lock
    def method_ssizessizearg(self, name, instance, i, j):
        instancePtr = self._store(instance)
        resultPtr = self.table[name](instancePtr, i, j)
        try:
            return self._return_retrieve(resultPtr)
        finally:
            self._cleanup(instancePtr, resultPtr)

    @lock
    def method_richcmp(self, name, instance, arg, op):
        instancePtr, argPtr = map(self._store, [instance, arg])
        resultPtr = self.table[name](instancePtr, argPtr, op)
        try:
            return self._return_retrieve(resultPtr)
        finally:
            self._cleanup(instancePtr, argPtr, resultPtr)

    @lock
    def method_hashfunc(self, name, instance):
        instancePtr = self._store(instance)
        result = self.table[name](instancePtr)
        try:
            return self._return(result)
        finally:
            self._cleanup(instancePtr)

    @lock
    def method_cmpfunc(self, name, instance, arg):
        instancePtr, argPtr = map(self._store, [instance, arg])
        result = self.table[name](instancePtr, argPtr)
        try:
            return self._return(result)
        finally:
            self._cleanup(instancePtr, argPtr)

    @lock
    def method_ssizeobjarg(self, name, instance, i, arg):
        instancePtr, argPtr = map(self._store, [instance, arg])
        result = self.table[name](instancePtr, i, argPtr)
        try:
            return self._return(result)
        finally:
            self._cleanup(instancePtr, argPtr)

    @lock
    def method_ssizessizeobjarg(self, name, instance, i, j, arg):
        instancePtr, argPtr = map(self._store, [instance, arg])
        result = self.table[name](instancePtr, i, j, argPtr)
        try:
            return self._return(result)
        finally:
            self._cleanup(instancePtr, argPtr)

    @lock
    def method_objobjarg(self, name, instance, arg1, arg2):
        instancePtr, arg1Ptr, arg2Ptr = map(self._store, [instance, arg1, arg2])
        result = self.table[name](instancePtr, arg1Ptr, arg2Ptr)
        try:
            return self._return(result)
        finally:
            self._cleanup(instancePtr, arg1Ptr, arg2Ptr)

    @lock
    def method_inquiry(self, name, instance):
        instancePtr = self._store(instance)
        result = self.table[name](instancePtr)
        try:
            return self._return(result)
        finally:
            self._cleanup(instancePtr)

    @lock
    def method_lenfunc(self, name, instance):
        instancePtr = self._store(instance)
        result = self.table[name](instancePtr)
        try:
            return self._return(result)
        finally:
            self._cleanup(instancePtr)

