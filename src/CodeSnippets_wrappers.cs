namespace Ironclad
{
    internal partial class CodeSnippets
    {
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

        public const string INQURY_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_inquiry('{2}{0}', self)
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
    }
}
