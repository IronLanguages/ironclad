namespace Ironclad
{
    internal partial class CodeSnippets
    {
        public const string FIX_CPyMarshal_RuntimeType_CODE = @"
CPyMarshal = CPyMarshal() # eww
";

        public const string FIX_math_log_log10_CODE = @"
import math
math._log = math.log
math.log = lambda x: math._log(float(x))
math._log10 = math.log10
math.log10 = lambda x: math._log10(float(x))
";

        public const string FAKE_numpy_testing_CODE = @"
class Tester():
    def test(self, *args, **kwargs):
        print msg
    def bench(self, *args, **kwargs):
        print msg
ScipyTest = NumpyTest = Tester
";

        public const string NOARGS_FUNCTION_CODE = @"
def {0}():
    '''{1}'''
    return _dispatcher.function_noargs('{2}{0}')
";

        public const string OBJARG_FUNCTION_CODE = @"
def {0}(arg):
    '''{1}'''
    return _dispatcher.function_objarg('{2}{0}', arg)
";

        public const string VARARGS_FUNCTION_CODE = @"
def {0}(*args):
    '''{1}'''
    return _dispatcher.function_varargs('{2}{0}', *args)
";

        public const string VARARGS_KWARGS_FUNCTION_CODE = @"
def {0}(*args, **kwargs):
    '''{1}'''
    return _dispatcher.function_kwargs('{2}{0}', *args, **kwargs)
";

        public const string NEW_EXCEPTION = @"
class {0}(Exception):
    __module__ = '{1}'
";

        public const string ACTUALISER_CODE = @"
class anon_actualiser(_ironclad_superclass):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __init__(self, *args, **kwargs):
        pass
    def __del__(self):
        pass
";

        public const string CLASS_CODE = @"
_anon_superclass = _ironclad_metaclass('anon', _ironclad_bases, dict())
class {0}_actualiser(_anon_superclass):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __init__(self, *args, **kwargs):
        pass
    def __del__(self):
        pass
    
class {0}(_anon_superclass):
    '''{2}'''
    __module__ = '{1}'
    def __new__(cls, *args, **kwargs):
        return cls._dispatcher.construct('{0}.tp_new', cls, *args, **kwargs)
    
    def __init__(self, *args, **kwargs):
        self._dispatcher.init('{0}.tp_init', self, *args, **kwargs)
    
    def __del__(self):
        self._dispatcher.delete(self)
";

        public const string MEMBER_GETTER_CODE = @"
    def {0}(self):
        return self._dispatcher.get_member_{2}(self, {1})
";

        public const string MEMBER_SETTER_CODE = @"
    def {0}(self, value):
        self._dispatcher.set_member_{2}(self, {1}, value)
";

        public const string GETTER_METHOD_CODE = @"
    def {0}(self):
        return self._dispatcher.method_getter('{1}{0}', self, IntPtr({2}))
";

        public const string SETTER_METHOD_CODE = @"
    def {0}(self, value):
        return self._dispatcher.method_setter('{1}{0}', self, value, IntPtr({2}))
";

        public const string PROPERTY_CODE = @"
    {0} = property({1}, {2}, None, '''{3}''')
";

        public const string GETITEM_CODE = @"
    def __getitem__(self, key):
        if hasattr(self, '_getitem_sq_item') and isinstance(key, int):
            return self._getitem_sq_item(key)
        if hasattr(self, '_getitem_mp_subscript'):
            return self._getitem_mp_subscript(key)
        raise IndexError('no idea how to index %s' % key)
";

        public const string SETITEM_CODE = @"
    def __setitem__(self, key, item):
        if hasattr(self, '_setitem_sq_ass_item') and isinstance(key, int):
            return self._setitem_sq_ass_item(key, item)
        if hasattr(self, '_setitem_mp_ass_subscript'):
            return self._setitem_mp_ass_subscript(key, item)
        raise IndexError('no idea how to index %s' % key)
";

        public const string ITER_METHOD_CODE = @"
    def __iter__(self):
        return self._dispatcher.method_selfarg('{0}tp_iter', self)
";

        public const string ITERNEXT_METHOD_CODE = @"
    def __raise_stop(self, resultPtr):
        if resultPtr == IntPtr(0) and self._dispatcher.mapper.LastException == None:
            raise StopIteration()

    def next(self):
        return self._dispatcher.method_selfarg('{0}tp_iternext', self, self.__raise_stop)
";

        public const string NOARGS_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_noargs('{2}{0}', self)
";

        public const string OBJARG_METHOD_CODE = @"
    def {0}(self, arg):
        '''{1}'''
        return self._dispatcher.method_objarg('{2}{0}', self, arg)
";

        public const string SWAPPEDOBJARG_METHOD_CODE = @"
    def {0}(self, arg):
        '''{1}'''
        return self._dispatcher.method_objarg('{2}{0}', arg, self)
";

        public const string VARARGS_METHOD_CODE = @"
    def {0}(self, *args):
        '''{1}'''
        return self._dispatcher.method_varargs('{2}{0}', self, *args)
";

        public const string VARARGS_KWARGS_METHOD_CODE = @"
    def {0}(self, *args, **kwargs):
        '''{1}'''
        return self._dispatcher.method_kwargs('{2}{0}', self, *args, **kwargs)
";

        public const string SSIZEARG_METHOD_CODE = @"
    def {0}(self, ssize):
        '''{1}'''
        return self._dispatcher.method_ssizearg('{2}{0}', self, ssize)
";

        public const string SSIZEOBJARG_METHOD_CODE = @"
    def {0}(self, ssize, obj):
        '''{1}'''
        return self._dispatcher.method_ssizeobjarg('{2}{0}', self, ssize, obj)
";

        public const string SSIZESSIZEARG_METHOD_CODE = @"
    def {0}(self, ssize1, ssize2):
        '''{1}'''
        return self._dispatcher.method_ssizessizearg('{2}{0}', self, ssize1, ssize2)
";

        public const string SSIZESSIZEOBJARG_METHOD_CODE = @"
    def {0}(self, ssize1, ssize2, obj):
        '''{1}'''
        return self._dispatcher.method_ssizessizeobjarg('{2}{0}', self, ssize1, ssize2, obj)
";

        public const string SELFARG_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_selfarg('{2}{0}', self)
";

        public const string LENFUNC_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_lenfunc('{2}{0}', self)
";

        public const string OBJOBJARG_METHOD_CODE = @"
    def {0}(self, arg1, arg2):
        '''{1}'''
        return self._dispatcher.method_objobjarg('{2}{0}', self, arg1, arg2)
";

        public const string TERNARY_METHOD_CODE = @"
    def {0}(self, arg1, arg2=None):
        '''{1}'''
        return self._dispatcher.method_ternary('{2}{0}', self, arg1, arg2)
";

        public const string SWAPPEDTERNARY_METHOD_CODE = @"
    def {0}(self, arg):
        '''{1}'''
        return self._dispatcher.method_ternary_swapped('{2}{0}', self, arg)
";

        public const string RICHCMP_METHOD_CODE = @"
    def __lt__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 0)
    def __le__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 1)
    def __eq__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 2)
    def __ne__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 3)
    def __gt__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 4)
    def __ge__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 5)
";

        public const string INQURY_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_inquiry('{2}{0}', self)
";

        public const string INSTALL_IMPORT_HOOK_CODE = @"
import ihooks
import imp

class _IroncladHooks(ihooks.Hooks):

    def get_suffixes(self):
        suffixes = [('.pyd', 'rb', imp.C_EXTENSION)]
        suffixes.extend(imp.get_suffixes())
        return suffixes

    def load_dynamic(self, name, filename, file):
        _mapper.LoadModule(filename, name)
        module = _mapper.GetModule(name)
        self.modules_dict()[name] = module
        return module


class _IroncladModuleImporter(ihooks.ModuleImporter):

    # copied from ihooks.py
    def determine_parent(self, globals):
        if not globals or not '__name__' in globals:
            return None
        pname = globals['__name__']
        if '__path__' in globals:
            parent = self.modules[pname]
            # 'assert globals is parent.__dict__' always fails --
            # I think an ipy module dict is some sort of funky 
            # wrapper around a Scope, so the underlying data store
            # actually is the same.
            assert len(globals) == len(parent.__dict__)
            for (k, v) in globals.iteritems():
                assert parent.__dict__[k] is v
            return parent
        if '.' in pname:
            i = pname.rfind('.')
            pname = pname[:i]
            parent = self.modules[pname]
            assert parent.__name__ == pname
            return parent
        return None

_importer = _IroncladModuleImporter()
_importer.set_hooks(_IroncladHooks())
_importer.install()
";

        public const string DISPATCHER_MODULE_CODE = @"
def lock(f):
    def locked(*args, **kwargs):
        MonitorEnter(Dispatcher._lock)
        try:
            return f(*args, **kwargs)
        finally:
            MonitorExit(Dispatcher._lock)
    return locked

Null = object()
NullPtr = IntPtr(0)

class Dispatcher(object):
    _lock = object() # this is effectively the GIL

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
        klassPtr, argsPtr, kwargsPtr = map(self._store, [klass, args, kwargs])
        instancePtr = self.table[name](klassPtr, argsPtr, kwargsPtr)
        try:
            self._check_error()
        finally:
            self._cleanup(argsPtr, kwargsPtr)
        
        if self.mapper.HasPtr(instancePtr):
            self.mapper.IncRef(instancePtr)
            return self._return_retrieve(instancePtr)
        
        instance = object.__new__(klass)
        self.mapper.StoreBridge(instancePtr, instance)
        self.mapper.Strengthen(instance)
        return instance

    @lock
    def init(self, name, instance, *args, **kwargs):
        if not self.table.has_key(name):
            return
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

        self.mapper.CheckBridgePtrs()
        self.mapper.DecRef(instancePtr)
        self.mapper.DecRef(instancePtr)
        self.mapper.Unmap(instancePtr)
        self._check_error()

    def dontDelete(self, _):
        pass

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

";
    }
}
