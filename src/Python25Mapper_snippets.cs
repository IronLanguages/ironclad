namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        private const string DISPATCHER_MODULE_CODE = @"
class Dispatcher(object):

    def __init__(self, mapper, table):
        self.mapper = mapper
        self.table = table

    def _maybe_raise(self, resultPtr):
        error = self.mapper.LastException
        if error:
            self.mapper.LastException = None
            raise error
        if resultPtr == nullPtr:
            raise NullReferenceException('CPython callable returned null without setting an exception')

    def _cleanup(self, *args):
        self.mapper.FreeTemps()
        for arg in args:
            if arg != nullPtr:
                self.mapper.DecRef(arg)

    def function_noargs(self, name):
        return self.method_noargs(name, nullPtr)

    def method_noargs(self, name, instancePtr):
        resultPtr = self.table[name](instancePtr, nullPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    def function_objarg(self, name, arg):
        return self.method_objarg(name, nullPtr, arg)
        
    def method_objarg(self, name, instancePtr, arg):
        argPtr = self.mapper.Store(arg)
        resultPtr = self.table[name](instancePtr, argPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argPtr)

    def function_varargs(self, name, *args):
        return self.method_varargs(name, nullPtr, *args)

    def method_varargs(self, name, instancePtr, *args):
        argsPtr = self.mapper.Store(args)
        resultPtr = self.table[name](instancePtr, argsPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argsPtr)

    def function_kwargs(self, name, *args, **kwargs):
        return self.method_kwargs(name, nullPtr, *args, **kwargs)

    def method_kwargs(self, name, instancePtr, *args, **kwargs):
        argsPtr = self.mapper.Store(args)
        kwargsPtr = nullPtr
        if kwargs != {}:
            kwargsPtr = self.mapper.Store(kwargs)
        resultPtr = self.table[name](instancePtr, argsPtr, kwargsPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argsPtr, kwargsPtr)
    
    def method_selfarg(self, name, instancePtr, errorHandler=None):
        resultPtr = self.table[name](instancePtr)
        try:
            if errorHandler:
                errorHandler(resultPtr)
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)


    def construct(self, name, klass, *args, **kwargs):
        instance = object.__new__(klass)
        argsPtr = self.mapper.Store(args)
        kwargsPtr = self.mapper.Store(kwargs)
        instancePtr = self.table[name](klass._typePtr, argsPtr, kwargsPtr)
        try:
            self._maybe_raise(instancePtr)
        finally:
            self._cleanup(argsPtr, kwargsPtr)
        
        self.mapper.StoreUnmanagedInstance(instancePtr, instance)
        instance._instancePtr = instancePtr
        return instance

    def init(self, name, instance, *args, **kwargs):
        argsPtr = self.mapper.Store(args)
        kwargsPtr = self.mapper.Store(kwargs)
        result = self.table[name](instance._instancePtr, argsPtr, kwargsPtr)
        self._cleanup(argsPtr, kwargsPtr)
        if result < 0:
            raise Exception('%s failed; object is probably not safe to use' % name)

";

        private const string NOARGS_FUNCTION_CODE = @"
def {0}():
    '''{1}'''
    return _dispatcher.function_noargs('{2}{0}')
";

        private const string OBJARG_FUNCTION_CODE = @"
def {0}(arg):
    '''{1}'''
    return _dispatcher.function_objarg('{2}{0}', arg)
";

        private const string VARARGS_FUNCTION_CODE = @"
def {0}(*args):
    '''{1}'''
    return _dispatcher.function_varargs('{2}{0}', *args)
";

        private const string VARARGS_KWARGS_FUNCTION_CODE = @"
def {0}(*args, **kwargs):
    '''{1}'''
    return _dispatcher.function_kwargs('{2}{0}', *args, **kwargs)
";

        private const string CLASS_CODE = @"
class {0}(object):
    '''{2}'''
    __module__ = '{1}'
    def __new__(cls, *args, **kwargs):
        return _dispatcher.construct('{0}.tp_new', cls, *args, **kwargs)
    
    def __init__(self, *args, **kwargs):
        _dispatcher.init('{0}.tp_init', self, *args, **kwargs)
";

        private const string ITER_METHOD_CODE = @"
    def __iter__(self):
        return _dispatcher.method_selfarg('{0}tp_iter', self._instancePtr)
";

        private const string ITERNEXT_METHOD_CODE = @"
    def __raise_stop(self, resultPtr):
        if resultPtr == nullPtr and _dispatcher.mapper.LastException == None:
                raise StopIteration()

    def next(self):
        return _dispatcher.method_selfarg('{0}tp_iternext', self._instancePtr, self.__raise_stop)
";

        private const string NOARGS_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return _dispatcher.method_noargs('{2}{0}', self._instancePtr)
";

        private const string OBJARG_METHOD_CODE = @"
    def {0}(self, arg):
        '''{1}'''
        return _dispatcher.method_objarg('{2}{0}', self._instancePtr, arg)
";

        private const string VARARGS_METHOD_CODE = @"
    def {0}(self, *args):
        '''{1}'''
        return _dispatcher.method_varargs('{2}{0}', self._instancePtr, *args)
";

        private const string VARARGS_KWARGS_METHOD_CODE = @"
    def {0}(self, *args, **kwargs):
        '''{1}'''
        return _dispatcher.method_kwargs('{2}{0}', self._instancePtr, *args, **kwargs)
";

        private const string CLASS_FIXUP_CODE = @"
{0}.__name__ = '{1}'
";
        
    }
}