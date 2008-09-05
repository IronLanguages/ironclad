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
        try:
            self._dispatcher.delete(self)
        except Exception, e:
            print 'error deleting object', self._instancePtr, type(self)
            print type(e), e
            print e.clsException.StackTrace
";

        public const string CLASS_BASES_CODE = @"
{0}.__bases__ += _ironclad_bases[1:]
";

        public const string MEMBER_GETTER_CODE = @"
    def {0}(self):
        fieldPtr = CPyMarshal.Offset(self._instancePtr, {1})
        return self._dispatcher.get_member_{2}(fieldPtr)
";

        public const string MEMBER_SETTER_CODE = @"
    def {0}(self, value):
        fieldPtr = CPyMarshal.Offset(self._instancePtr, {1})
        self._dispatcher.set_member_{2}(fieldPtr, value)
";

        public const string GETTER_METHOD_CODE = @"
    def {0}(self):
        return self._dispatcher.method_getter('{1}{0}', self._instancePtr, IntPtr({2}))
";

        public const string SETTER_METHOD_CODE = @"
    def {0}(self, value):
        return self._dispatcher.method_setter('{1}{0}', self._instancePtr, value, IntPtr({2}))
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
        return self._dispatcher.method_selfarg('{0}tp_iter', self._instancePtr)
";

        public const string ITERNEXT_METHOD_CODE = @"
    def __raise_stop(self, resultPtr):
        if resultPtr == IntPtr(0) and self._dispatcher.mapper.LastException == None:
            raise StopIteration()

    def next(self):
        return self._dispatcher.method_selfarg('{0}tp_iternext', self._instancePtr, self.__raise_stop)
";

        public const string NOARGS_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_noargs('{2}{0}', self._instancePtr)
";

        public const string OBJARG_METHOD_CODE = @"
    def {0}(self, arg):
        '''{1}'''
        return self._dispatcher.method_objarg('{2}{0}', self._instancePtr, arg)
";

        public const string SWAPPEDOBJARG_METHOD_CODE = @"
    def {0}(self, arg):
        '''{1}'''
        return self._dispatcher.method_objarg_swapped('{2}{0}', self._instancePtr, arg)
";

        public const string VARARGS_METHOD_CODE = @"
    def {0}(self, *args):
        '''{1}'''
        return self._dispatcher.method_varargs('{2}{0}', self._instancePtr, *args)
";

        public const string VARARGS_KWARGS_METHOD_CODE = @"
    def {0}(self, *args, **kwargs):
        '''{1}'''
        return self._dispatcher.method_kwargs('{2}{0}', self._instancePtr, *args, **kwargs)
";

        public const string SSIZEARG_METHOD_CODE = @"
    def {0}(self, ssize):
        '''{1}'''
        return self._dispatcher.method_ssizearg('{2}{0}', self._instancePtr, ssize)
";

        public const string SSIZEOBJARG_METHOD_CODE = @"
    def {0}(self, ssize, obj):
        '''{1}'''
        return self._dispatcher.method_ssizeobjarg('{2}{0}', self._instancePtr, ssize, obj)
";

        public const string SSIZESSIZEARG_METHOD_CODE = @"
    def {0}(self, ssize1, ssize2):
        '''{1}'''
        return self._dispatcher.method_ssizessizearg('{2}{0}', self._instancePtr, ssize1, ssize2)
";

        public const string SSIZESSIZEOBJARG_METHOD_CODE = @"
    def {0}(self, ssize1, ssize2, obj):
        '''{1}'''
        return self._dispatcher.method_ssizessizeobjarg('{2}{0}', self._instancePtr, ssize1, ssize2, obj)
";

        public const string SELFARG_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_selfarg('{2}{0}', self._instancePtr)
";

        public const string LENFUNC_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_lenfunc('{2}{0}', self._instancePtr)
";

        public const string OBJOBJARG_METHOD_CODE = @"
    def {0}(self, arg1, arg2):
        '''{1}'''
        return self._dispatcher.method_objobjarg('{2}{0}', self._instancePtr, arg1, arg2)
";

        public const string TERNARY_METHOD_CODE = @"
    def {0}(self, arg1, arg2=None):
        '''{1}'''
        return self._dispatcher.method_ternary('{2}{0}', self._instancePtr, arg1, arg2)
";

        public const string SWAPPEDTERNARY_METHOD_CODE = @"
    def {0}(self, arg):
        '''{1}'''
        return self._dispatcher.method_ternary_swapped('{2}{0}', self._instancePtr, arg)
";

        public const string RICHCMP_METHOD_CODE = @"
    def __lt__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self._instancePtr, other, 0)
    def __le__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self._instancePtr, other, 1)
    def __eq__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self._instancePtr, other, 2)
    def __ne__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self._instancePtr, other, 3)
    def __gt__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self._instancePtr, other, 4)
    def __ge__(self, other):
        return self._dispatcher.method_richcmp('{0}tp_richcompare', self._instancePtr, other, 5)
";

        public const string INQURY_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_inquiry('{2}{0}', self._instancePtr)
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

class Dispatcher(object):
    _lock = object()

    def __init__(self, mapper, table):
        self.mapper = mapper
        self.table = table

    def _maybe_raise(self, resultPtr=None):
        error = self.mapper.LastException
        if error:
            self.mapper.LastException = None
            raise error
        if resultPtr == IntPtr(0):
            raise NullReferenceException('CPython callable returned null without setting an exception')

    def _surely_raise(self, fallbackError):
        error = self.mapper.LastException
        if error:
            self.mapper.LastException = None
            raise error
        raise fallbackError

    def _cleanup(self, *args):
        self.mapper.FreeTemps()
        for arg in args:
            if arg != IntPtr(0):
                self.mapper.DecRef(arg)
    
    @lock
    def construct(self, name, klass, *args, **kwargs):
        instance = object.__new__(klass)
        argsPtr = self.mapper.Store(args)
        kwargsPtr = self.mapper.Store(kwargs)
        instancePtr = self.table[name](klass._typePtr, argsPtr, kwargsPtr)
        try:
            self._maybe_raise(instancePtr)
        finally:
            self._cleanup(argsPtr, kwargsPtr)
        
        if self.mapper.HasPtr(instancePtr):
            self.mapper.IncRef(instancePtr)
            return self.mapper.Retrieve(instancePtr)
        
        instance._instancePtr = instancePtr
        self.mapper.StoreBridge(instancePtr, instance)
        self.mapper.Strengthen(instance)
        return instance

    @lock
    def init(self, name, instance, *args, **kwargs):
        if not self.table.has_key(name):
            return
        argsPtr = self.mapper.Store(args)
        kwargsPtr = self.mapper.Store(kwargs)
        result = self.table[name](instance._instancePtr, argsPtr, kwargsPtr)
        self._cleanup(argsPtr, kwargsPtr)
            
        if result < 0:
            self._surely_raise(Exception('%s failed; object is probably not safe to use' % name))

    @lock
    def delete(self, instance):
        self.mapper.CheckBridgePtrs()
        self.mapper.DecRef(instance._instancePtr)
        self.mapper.Unmap(instance._instancePtr)

    def dontDelete(_, __):
        pass

    def function_noargs(self, name):
        return self.method_noargs(name, IntPtr(0))

    @lock
    def method_noargs(self, name, instancePtr):
        resultPtr = self.table[name](instancePtr, IntPtr(0))
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    def function_objarg(self, name, arg):
        return self.method_objarg(name, IntPtr(0), arg)
        
    @lock
    def method_objarg(self, name, instancePtr, arg):
        argPtr = self.mapper.Store(arg)
        resultPtr = self.table[name](instancePtr, argPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argPtr)
        
    @lock
    def method_objarg_swapped(self, name, instancePtr, arg):
        argPtr = self.mapper.Store(arg)
        resultPtr = self.table[name](argPtr, instancePtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argPtr)

    def function_varargs(self, name, *args):
        return self.method_varargs(name, IntPtr(0), *args)

    @lock
    def method_varargs(self, name, instancePtr, *args):
        argsPtr = self.mapper.Store(args)
        resultPtr = self.table[name](instancePtr, argsPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argsPtr)

    def function_kwargs(self, name, *args, **kwargs):
        return self.method_kwargs(name, IntPtr(0), *args, **kwargs)

    @lock
    def method_kwargs(self, name, instancePtr, *args, **kwargs):
        argsPtr = self.mapper.Store(args)
        kwargsPtr = IntPtr(0)
        if kwargs != {}:
            kwargsPtr = self.mapper.Store(kwargs)
        resultPtr = self.table[name](instancePtr, argsPtr, kwargsPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argsPtr, kwargsPtr)
    
    @lock
    def method_selfarg(self, name, instancePtr, errorHandler=None):
        resultPtr = self.table[name](instancePtr)
        try:
            if errorHandler:
                errorHandler(resultPtr)
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    @lock
    def method_ssizearg(self, name, instancePtr, i):
        resultPtr = self.table[name](instancePtr, i)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    @lock
    def method_ssizeobjarg(self, name, instancePtr, i, arg):
        argPtr = self.mapper.Store(arg)
        result = self.table[name](instancePtr, i, argPtr)
        try:
            self._maybe_raise()
            return result
        finally:
            self._cleanup(argPtr)

    @lock
    def method_ssizessizearg(self, name, instancePtr, i, j):
        resultPtr = self.table[name](instancePtr, i, j)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    @lock
    def method_ssizessizeobjarg(self, name, instancePtr, i, j, arg):
        argPtr = self.mapper.Store(arg)
        result = self.table[name](instancePtr, i, j, argPtr)
        try:
            self._maybe_raise()
            return result
        finally:
            self._cleanup(argPtr)

    @lock
    def method_objobjarg(self, name, instancePtr, arg1, arg2):
        arg1Ptr = self.mapper.Store(arg1)
        arg2Ptr = self.mapper.Store(arg2)
        result = self.table[name](instancePtr, arg1Ptr, arg2Ptr)
        try:
            self._maybe_raise()
            return result
        finally:
            self._cleanup(arg1Ptr, arg2Ptr)

    @lock
    def method_inquiry(self, name, instancePtr):
        result = self.table[name](instancePtr)
        self._maybe_raise()
        return result

    @lock
    def method_ternary(self, name, instancePtr, arg1, arg2):
        arg1Ptr = self.mapper.Store(arg1)
        arg2Ptr = self.mapper.Store(arg2)
        resultPtr = self.table[name](instancePtr, arg1Ptr, arg2Ptr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, arg1Ptr, arg2Ptr)

    @lock
    def method_ternary_swapped(self, name, instancePtr, arg):
        argPtr = self.mapper.Store(arg)
        resultPtr = self.table[name](argPtr, instancePtr, IntPtr(0))
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argPtr)

    @lock
    def method_richcmp(self, name, instancePtr, arg1, op):
        arg1Ptr = self.mapper.Store(arg1)
        resultPtr = self.table[name](instancePtr, arg1Ptr, op)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, arg1Ptr)

    @lock
    def method_lenfunc(self, name, instancePtr):
        result = self.table[name](instancePtr)
        self._maybe_raise()
        return result

    @lock
    def method_getter(self, name, instancePtr, closurePtr):
        resultPtr = self.table[name](instancePtr, closurePtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    @lock
    def method_setter(self, name, instancePtr, value, closurePtr):
        valuePtr = self.mapper.Store(value)
        result = self.table[name](instancePtr, valuePtr, closurePtr)
        self._cleanup(valuePtr)
        if result < 0:
            self._surely_raise(Exception('%s failed' % name))


    @lock
    def set_member_int(self, address, value):
        CPyMarshal.WriteInt(address, value)

    @lock
    def get_member_int(self, address):
        return CPyMarshal.ReadInt(address)

    @lock
    def set_member_char(self, address, value):
        CPyMarshal.WriteByte(address, ord(value))

    @lock
    def get_member_char(self, address):
        return chr(CPyMarshal.ReadByte(address))

    @lock
    def set_member_ubyte(self, address, value):
        CPyMarshal.WriteByte(address, value)

    @lock
    def get_member_ubyte(self, address):
        return CPyMarshal.ReadByte(address)

    @lock
    def set_member_object(self, address, value):
        valuePtr = self.mapper.Store(value)
        oldvPtr = CPyMarshal.ReadPtr(address)
        CPyMarshal.WritePtr(address, valuePtr)
        if oldvPtr != IntPtr(0):
            self.mapper.DecRef(oldvPtr)

    @lock
    def get_member_object(self, address):
        valuePtr = CPyMarshal.ReadPtr(address)
        if valuePtr != IntPtr(0):
            return self.mapper.Retrieve(valuePtr)

";
    }
}
